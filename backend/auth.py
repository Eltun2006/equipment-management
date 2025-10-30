from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import or_

from .models import db, User
from .utils import hash_password, verify_password, is_valid_email


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
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

    existing = db.session.scalar(db.select(User).where(or_(User.username == username, User.email == email)))
    if existing:
        return jsonify({"message": "Username or email already in use."}), 400

    user = User(username=username, email=email, password=hash_password(password), full_name=full_name)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully."}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(force=True)
    login_id = (data.get("login") or data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not login_id or not password:
        return jsonify({"message": "Login and password are required."}), 400

    user = db.session.scalar(db.select(User).where(or_(User.username == login_id, User.email == login_id.lower())))
    if not user or not verify_password(password, user.password):
        return jsonify({"message": "Invalid credentials."}), 401

    # Use string subject for compatibility; put extras in additional claims
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


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # Stateless JWT: client should delete token; implement token blocklist if needed
    return jsonify({"message": "Logged out."})


@auth_bp.get("/me")
@jwt_required()
def me():
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
