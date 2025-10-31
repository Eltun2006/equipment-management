from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from sqlalchemy import func

from .models import db, Comment, Equipment, User


socketio: SocketIO | None = None


def init_socketio(sio: SocketIO):
    global socketio
    socketio = sio


# Optional: allow joining rooms per equipment to reduce traffic

def register_socket_handlers(sio: SocketIO):
    @sio.on("connect")
    def on_connect():
        emit("connected", {"sid": request.sid})

    @sio.on("join_equipment")
    def on_join_equipment(data):
        room = f"equipment_{data.get('equipment_id')}"
        join_room(room)

    @sio.on("leave_equipment")
    def on_leave_equipment(data):
        room = f"equipment_{data.get('equipment_id')}"
        leave_room(room)


def broadcast_new_comment(comment: Comment):
    if not socketio:
        return
    # Send to the equipment room and globally update counts
    room = f"equipment_{comment.equipment_id}"

    # Get username
    user = db.get(User, comment.user_id)
    payload = {
        "id": comment.id,
        "equipment_id": comment.equipment_id,
        "user_id": comment.user_id,
        "username": user.username if user else "",
        "comment_text": comment.comment_text,
        "created_at": comment.created_at.isoformat(),
    }

    socketio.emit("new_comment", payload, room=room, broadcast=True)

    # Also emit count update for equipment list
    count = db.session.scalar(db.select(func.count()).where(Comment.equipment_id == comment.equipment_id)) or 0
    socketio.emit("comment_count_updated", {"equipment_id": comment.equipment_id, "count": count}, broadcast=True)


def broadcast_comment_deleted(comment_id: int, equipment_id: int):
    if not socketio:
        return
    room = f"equipment_{equipment_id}"
    socketio.emit("comment_deleted", {"id": comment_id, "equipment_id": equipment_id}, room=room, broadcast=True)

    count = db.session.scalar(db.select(func.count()).where(Comment.equipment_id == equipment_id)) or 0
    socketio.emit("comment_count_updated", {"equipment_id": equipment_id, "count": count}, broadcast=True)


