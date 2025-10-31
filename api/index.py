"""
Vercel serverless function - Main Flask API entry point
Routes all /api/* requests through this handler
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_, func, desc
from math import ceil
from io import BytesIO
from datetime import datetime, date
from uuid import uuid4
import json

from lib.database import db, get_app_config
from lib.models import User, Equipment, Comment
from lib.utils import hash_password, verify_password, is_valid_email, generate_excel_template, parse_excel_to_rows, validate_import_rows, VALID_STATUSES
from openpyxl import Workbook

# Create Flask app
app = Flask(__name__)
config = get_app_config()
app.config.update(config)

# Initialize extensions
db.init_app(app)
JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

# Initialize database on first request
_initialized = False

def init_database():
    global _initialized
    if _initialized:
        return
    
    with app.app_context():
        db.create_all()
        # Ensure 'extra' column exists
        try:
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            if db.engine.dialect.has_table(db.engine, 'equipment'):
                cols = {c['name'] for c in insp.get_columns('equipment')}
                if 'extra' not in cols:
                    with db.engine.begin() as conn:
                        try:
                            conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra JSON")
                        except Exception:
                            conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra TEXT")
        except Exception:
            pass
        
        # Seed data
        try:
            if not db.session.scalar(db.select(User).where(User.username == "admin")):  # type: ignore
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    password=hash_password("Admin@123"),
                    full_name="Administrator",
                    role="admin",
                )
                db.session.add(admin)
            if not db.session.scalar(db.select(User).where(User.username == "user")):  # type: ignore
                user = User(
                    username="user",
                    email="user@example.com",
                    password=hash_password("User@123"),
                    full_name="Standard User",
                    role="user",
                )
                db.session.add(user)
            
            if not db.session.scalar(db.select(Equipment)):  # type: ignore
                samples = [
                    Equipment(equipment_name="Laptop X", equipment_code="EQ-001", category="Computers", location="London", status="Active", description="Dell Latitude 7420"),
                    Equipment(equipment_name="Forklift A", equipment_code="EQ-002", category="Vehicles", location="Warehouse A", status="Repair", description="Hydraulic leak"),
                    Equipment(equipment_name="Router R1", equipment_code="EQ-003", category="Network", location="Data Center", status="Active", description="Core router"),
                ]
                db.session.add_all(samples)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    
    _initialized = True

# Health check
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Auth routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    init_database()
    try:
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        full_name = (data.get("full_name") or "").strip()

        if len(password) < 6:
            return jsonify({"message": "Password must be at least 6 characters."}), 400
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email address."}), 400
        if not username:
            return jsonify({"message": "Username is required."}), 400

        existing = db.session.scalar(db.select(User).where(or_(User.username == username, User.email == email)))  # type: ignore
        if existing:
            return jsonify({"message": "Username or email already in use."}), 400

        user = User(username=username, email=email, password=hash_password(password), full_name=full_name)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "Registered successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    init_database()
    try:
        data = request.get_json(force=True)
        login_id = (data.get("login") or data.get("username") or data.get("email") or "").strip()
        password = data.get("password") or ""

        if not login_id or not password:
            return jsonify({"message": "Login and password are required."}), 400

        user = db.session.scalar(db.select(User).where(or_(User.username == login_id, User.email == login_id.lower())))  # type: ignore
        if not user or not verify_password(password, user.password):
            return jsonify({"message": "Invalid credentials."}), 401

        token = create_access_token(
            identity=str(user.id),
            additional_claims={"username": user.username, "role": user.role}
        )

        return jsonify({
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }
        })
    except Exception as e:
        return jsonify({"message": f"Login failed: {str(e)}"}), 500

@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out."})

@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    init_database()
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at.isoformat(),
    })

# Equipment routes
@app.route("/api/equipment", methods=["GET"])
@jwt_required()
def list_equipment():
    init_database()
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    status = (request.args.get("status") or "").strip()
    comment_count = (request.args.get("comment_count") or "").strip()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    stmt = db.select(Equipment)  # type: ignore

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

    total = db.session.scalar(db.select(func.count()).select_from(stmt.subquery())) or 0  # type: ignore

    stmt = stmt.order_by(Equipment.updated_at.desc()).limit(per_page).offset((page - 1) * per_page)  # type: ignore
    items = db.session.scalars(stmt).all()  # type: ignore

    counts_by_id = {r[0]: r[1] for r in db.session.query(Comment.equipment_id, func.count(Comment.id)).group_by(Comment.equipment_id).all()}

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

@app.route("/api/equipment/<int:eid>", methods=["GET"])
@jwt_required()
def get_equipment(eid: int):
    init_database()
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

@app.route("/api/equipment/import", methods=["POST"])
@jwt_required()
def import_excel():
    init_database()
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

    column_map_str = request.form.get("column_map")
    try:
        column_map = json.loads(column_map_str) if column_map_str else {}
    except Exception:
        column_map = {}

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

    incoming_codes = {r["equipment_code"] for r in rows if r.get("equipment_code") and r.get("equipment_code") != "0"}
    if incoming_codes:
        existing_codes = set(
            c for (c,) in db.session.query(Equipment.equipment_code).filter(Equipment.equipment_code.in_(incoming_codes)).all()
        )
        duplicates = sorted(incoming_codes.intersection(existing_codes))
        if duplicates:
            return jsonify({"errors": [f"Duplicate codes in database: {', '.join(duplicates)}"]}), 400

    existing_codes = set(c for (c,) in db.session.query(Equipment.equipment_code).all())
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

@app.route("/api/equipment/<int:eid>", methods=["PUT"])
@jwt_required()
def update_equipment(eid: int):
    init_database()
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

@app.route("/api/equipment/<int:eid>", methods=["DELETE"])
@jwt_required()
def delete_equipment(eid: int):
    init_database()
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

@app.route("/api/equipment/template", methods=["GET"])
@jwt_required()
def download_template():
    data = generate_excel_template()
    return send_file(
        BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="equipment_template.xlsx"
    )

@app.route("/api/equipment/export", methods=["GET"])
@jwt_required()
def export_equipment():
    init_database()
    identity = get_jwt_identity()
    try:
        _ = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401

    items = db.session.scalars(db.select(Equipment).order_by(Equipment.id.asc())).all()  # type: ignore

    wb = Workbook()
    ws = wb.active
    ws.title = "Equipment"

    columns = [col.name for col in Equipment.__table__.columns]
    ws.append(columns)

    for e in items:
        values = []
        for col in columns:
            v = getattr(e, col, "")
            if isinstance(v, (datetime, date)):
                v = v.isoformat()
            elif v is None:
                v = ""
            values.append(v)
        ws.append(values)

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

# Comments routes
@app.route("/api/comments/equipment/<int:eid>", methods=["GET"])
@jwt_required()
def list_comments(eid: int):
    init_database()
    db.get_or_404(Equipment, eid)
    comments = db.session.scalars(
        db.select(Comment).where(Comment.equipment_id == eid).order_by(desc(Comment.created_at))  # type: ignore
    ).all()
    user_ids = {c.user_id for c in comments}
    users = {u.id: u for u in db.session.scalars(db.select(User).where(User.id.in_(user_ids))).all()}  # type: ignore

    return jsonify([
        {
            "id": c.id,
            "equipment_id": c.equipment_id,
            "user_id": c.user_id,
            "username": users.get(c.user_id).username if users.get(c.user_id) else "",
            "comment_text": c.comment_text,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ])

@app.route("/api/comments", methods=["POST"])
@jwt_required()
def add_comment():
    init_database()
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)

    data = request.get_json(force=True)
    equipment_id = data.get("equipment_id")
    text = (data.get("comment_text") or "").strip()

    if not equipment_id:
        return jsonify({"message": "equipment_id is required."}), 400
    if not text:
        return jsonify({"message": "comment_text is required."}), 400
    db.get_or_404(Equipment, equipment_id)

    comment = Comment(equipment_id=equipment_id, user_id=user.id, comment_text=text)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "id": comment.id,
        "equipment_id": comment.equipment_id,
        "user_id": comment.user_id,
        "username": user.username,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at.isoformat(),
    }), 201

@app.route("/api/comments/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_comment(cid: int):
    init_database()
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)

    comment = db.get_or_404(Comment, cid)
    if comment.user_id != user.id and user.role != "admin":
        return jsonify({"message": "Not allowed."}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Deleted."})

# Export app for Vercel
# Vercel will automatically detect the Flask app
if __name__ == "__main__":
    app.run(debug=True)

