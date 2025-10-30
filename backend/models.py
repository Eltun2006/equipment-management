from datetime import datetime
from typing import Optional

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'admin' or 'user'

    comments = db.relationship("Comment", backref="user", lazy=True, cascade="all,delete")

    def is_admin(self) -> bool:
        return self.role == "admin"


class Equipment(db.Model, TimestampMixin):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(200), nullable=False)
    equipment_code = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Active")
    description = db.Column(db.Text, nullable=True)
    imported_at = db.Column(db.DateTime, nullable=True)
    # Dynamic fields container (JSON)
    extra = db.Column(db.JSON, default=dict)

    comments = db.relationship("Comment", backref="equipment", lazy=True, cascade="all,delete")


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
