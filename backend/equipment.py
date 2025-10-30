from datetime import datetime
from math import ceil
from typing import Dict

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from io import BytesIO
from sqlalchemy import or_, func

from .models import db, Equipment, Comment, User
from .utils import generate_excel_template, parse_excel_to_rows, validate_import_rows, VALID_STATUSES
from openpyxl import Workbook


equipment_bp = Blueprint("equipment", __name__, url_prefix="/api/equipment")


@equipment_bp.get("")
@jwt_required()
def list_equipment():
    # Filters
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    status = (request.args.get("status") or "").strip()
    comment_count = (request.args.get("comment_count") or "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    stmt = db.select(Equipment)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Equipment.equipment_name.ilike(like),
            Equipment.equipment_code.ilike(like),
            Equipment.location.ilike(like),
        ))
    if category:
        stmt = stmt.where(Equipment.category == category)
    if status:
        stmt = stmt.where(Equipment.status == status)

    # Comment count filtering with HAVING
    sub = db.session.query(
        Comment.equipment_id.label("eid"), func.count(Comment.id).label("cc")
    ).group_by(Comment.equipment_id).subquery()

    stmt = stmt.outerjoin(sub, Equipment.id == sub.c.eid)

    if comment_count:
        try:
            cc = int(comment_count)
            if cc == 0:
                stmt = stmt.where((sub.c.cc == None))  # noqa: E711
            elif cc == 1:
                stmt = stmt.where(sub.c.cc == 1)
            elif cc == 2:
                stmt = stmt.where(sub.c.cc == 2)
            elif cc >= 3:
                stmt = stmt.where(sub.c.cc >= 3)
        except ValueError:
            pass

    total = db.session.scalar(db.select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(Equipment.updated_at.desc()).limit(per_page).offset((page - 1) * per_page)
    items = db.session.scalars(stmt).all()

    # Preload comment counts
    counts_by_id = {r[0]: r[1] for r in db.session.query(Comment.equipment_id, func.count(Comment.id)).group_by(Comment.equipment_id).all()}

    # Collect dynamic headers from extras of the current page
    dynamic_headers = []
    seen_hdr = set()
    for e in items:
        if isinstance(e.extra, dict):
            for k in e.extra.keys():
                if k not in seen_hdr and k not in {"id", "created_at", "updated_at"}:
                    seen_hdr.add(k)
                    dynamic_headers.append(k)

    return jsonify({
        "items": [
            {
                "id": e.id,
                "equipment_name": e.equipment_name,
                "equipment_code": e.equipment_code,
                "category": e.category,
                "location": e.location,
                "status": e.status,
                "description": e.description,
                "comment_count": counts_by_id.get(e.id, 0),
                "extra": e.extra or {},
                "updated_at": e.updated_at.isoformat(),
            } for e in items
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": ceil(total / per_page) if per_page else 1,
        "filters": {
            "statuses": sorted(VALID_STATUSES),
        },
        "dynamic_headers": dynamic_headers,
    })


@equipment_bp.get("/<int:eid>")
@jwt_required()
def get_equipment(eid: int):
    e = db.get_or_404(Equipment, eid)
    return jsonify({
        "id": e.id,
        "equipment_name": e.equipment_name,
        "equipment_code": e.equipment_code,
        "category": e.category,
        "location": e.location,
        "status": e.status,
        "description": e.description,
        "imported_at": e.imported_at.isoformat() if e.imported_at else None,
        "updated_at": e.updated_at.isoformat(),
    })


@equipment_bp.post("/import")
@jwt_required()
def import_excel():
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)
    if user.role != "admin":
        return jsonify({"message": "Only admins can import."}), 403

    if "file" not in request.files:
        return jsonify({"message": "No file uploaded."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        return jsonify({"message": "Invalid file type. Upload .xlsx or .xls."}), 400

    column_map: Dict[str, str] = request.form.get("column_map")
    try:
        # column_map comes as JSON string if provided
        import json
        column_map = json.loads(column_map) if column_map else {}
    except Exception:
        column_map = {}

    # Parse and validate with safe error handling
    try:
        data = file.read()
        if not data:
            return jsonify({"message": "Uploaded file is empty."}), 400
        df = parse_excel_to_rows(BytesIO(data))
        rows, errors = validate_import_rows(df, column_map)
    except Exception as exc:
        return jsonify({"message": f"Failed to read Excel: {type(exc).__name__}: {str(exc)}"}), 400
    if errors:
        return jsonify({"errors": errors}), 400

    # Check duplicates against DB
    incoming_codes = {r["equipment_code"] for r in rows if r.get("equipment_code") and r.get("equipment_code") != "0"}
    if incoming_codes:
        existing_codes = set(
            c for (c,) in db.session.query(Equipment.equipment_code).filter(Equipment.equipment_code.in_(incoming_codes)).all()
        )
        duplicates = sorted(incoming_codes.intersection(existing_codes))
        if duplicates:
            return jsonify({"errors": [f"Duplicate codes in database: {', '.join(duplicates)}"]}), 400

    # Normalize and ensure unique equipment_code values; generate for blanks/'0'/duplicates
    from uuid import uuid4
    existing_codes = set(
        c for (c,) in db.session.query(Equipment.equipment_code).all()
    )
    used_in_batch = set()
    for idx, r in enumerate(rows):
        name = (r.get("equipment_name") or "").strip()
        if not name:
            r["equipment_name"] = f"Item {idx+1}"
        code = (r.get("equipment_code") or "").strip()
        if not code or code == "0" or code in existing_codes or code in used_in_batch:
            new_code = f"AUTO-{uuid4().hex[:8].upper()}"
            r["equipment_code"] = new_code
            used_in_batch.add(new_code)
        else:
            used_in_batch.add(code)
            existing_codes.add(code)

    # Bulk insert
    try:
        objects = [
            Equipment(
                equipment_name=r["equipment_name"],
                equipment_code=r["equipment_code"],
                category=r["category"],
                location=r["location"],
                status=r["status"],
                description=r["description"],
                imported_at=r["imported_at"],
                extra=r.get("extra", {}),
            ) for r in rows
        ]
        db.session.add_all(objects)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"message": f"Failed to save import: {type(exc).__name__}: {str(exc)}"}), 500

    return jsonify({"message": f"Imported {len(objects)} items successfully."})


@equipment_bp.put("/<int:eid>")
@jwt_required()
def update_equipment(eid: int):
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)
    e = db.get_or_404(Equipment, eid)

    data = request.get_json(force=True)
    if user.role != "admin":
        return jsonify({"message": "Only admins can update."}), 403

    for field in ["equipment_name", "category", "location", "status", "description"]:
        if field in data:
            setattr(e, field, data[field])

    db.session.commit()
    return jsonify({"message": "Updated."})


@equipment_bp.delete("/<int:eid>")
@jwt_required()
def delete_equipment(eid: int):
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)
    if user.role != "admin":
        return jsonify({"message": "Only admins can delete."}), 403

    e = db.get_or_404(Equipment, eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Deleted."})


@equipment_bp.get("/template")
@jwt_required()
def download_template():
    data = generate_excel_template()
    return send_file(BytesIO(data), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="equipment_template.xlsx")


@equipment_bp.get("/export")
@jwt_required()
def export_equipment():
    # Authenticate
    identity = get_jwt_identity()
    try:
        _ = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401

    # Fetch all equipment
    items = db.session.scalars(db.select(Equipment).order_by(Equipment.id.asc())).all()

    # Build workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Equipment"

    # Dynamically read ALL columns from the model/table
    columns = [col.name for col in Equipment.__table__.columns]
    ws.append(columns)

    from datetime import date, datetime as dt

    for e in items:
        values = []
        for col in columns:
            v = getattr(e, col, "")
            if isinstance(v, (dt, date)):
                v = v.isoformat()
            elif v is None:
                v = ""
            values.append(v)
        ws.append(values)

    # Serialize to bytes
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    today = datetime.utcnow().date().isoformat()
    filename = f"equipment_export_{today}.xlsx"
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )
