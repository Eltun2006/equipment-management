from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import desc

from .models import db, Comment, Equipment, User
from .socketio_events import broadcast_new_comment, broadcast_comment_deleted


comments_bp = Blueprint("comments", __name__, url_prefix="/api/comments")


@comments_bp.get("/equipment/<int:eid>")
@jwt_required()
def list_comments(eid: int):
    db.get_or_404(Equipment, eid)
    comments = db.session.scalars(
        db.select(Comment).where(Comment.equipment_id == eid).order_by(desc(Comment.created_at))
    ).all()
    user_ids = {c.user_id for c in comments}
    users = {u.id: u for u in db.session.scalars(db.select(User).where(User.id.in_(user_ids))).all()}

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


@comments_bp.post("")
@jwt_required()
def add_comment():
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

    broadcast_new_comment(comment)

    return jsonify({
        "id": comment.id,
        "equipment_id": comment.equipment_id,
        "user_id": comment.user_id,
        "username": user.username,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at.isoformat(),
    }), 201


@comments_bp.delete("/<int:cid>")
@jwt_required()
def delete_comment(cid: int):
    identity = get_jwt_identity()
    try:
        uid = int(identity)
    except Exception:
        return jsonify({"message": "Invalid token."}), 401
    user = db.get_or_404(User, uid)

    comment = db.get_or_404(Comment, cid)
    if comment.user_id != user.id and user.role != "admin":
        return jsonify({"message": "Not allowed."}), 403

    equipment_id = comment.equipment_id
    db.session.delete(comment)
    db.session.commit()

    broadcast_comment_deleted(cid, equipment_id)

    return jsonify({"message": "Deleted."})
