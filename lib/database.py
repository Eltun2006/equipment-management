import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_app_config():
    """Get configuration dict for Flask app"""
    from lib.config import Config
    return {
        "SECRET_KEY": Config.SECRET_KEY,
        "JWT_SECRET_KEY": Config.JWT_SECRET_KEY,
        "JWT_ACCESS_TOKEN_EXPIRES": Config.JWT_ACCESS_TOKEN_EXPIRES,
        "SQLALCHEMY_DATABASE_URI": Config.SQLALCHEMY_DATABASE_URI,
        "SQLALCHEMY_ECHO": Config.SQLALCHEMY_ECHO,
        "SQLALCHEMY_TRACK_MODIFICATIONS": Config.SQLALCHEMY_TRACK_MODIFICATIONS,
        "UPLOADED_EXCELS_DEST": Config.UPLOADED_EXCELS_DEST,
        "MAX_CONTENT_LENGTH": Config.MAX_CONTENT_LENGTH,
    }

def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    # Create tables and seed data
    with app.app_context():
        db.create_all()
        # Ensure 'extra' column exists
        try:
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            cols = {c['name'] for c in insp.get_columns('equipment')}
            if 'extra' not in cols:
                with db.engine.begin() as conn:
                    try:
                        conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra JSON")
                    except Exception:
                        conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra TEXT")
        except Exception:
            pass
        seed_data()

def seed_data():
    """Seed initial data if database is empty"""
    from lib.models import User, Equipment
    from lib.utils import hash_password
    
    # Users
    if not db.session.scalar(db.select(User).where(User.username == "admin")):
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hash_password("Admin@123"),
            full_name="Administrator",
            role="admin",
        )
        db.session.add(admin)
    if not db.session.scalar(db.select(User).where(User.username == "user")):
        user = User(
            username="user",
            email="user@example.com",
            password=hash_password("User@123"),
            full_name="Standard User",
            role="user",
        )
        db.session.add(user)

    # Equipment
    if not db.session.scalar(db.select(Equipment)):
        samples = [
            Equipment(equipment_name="Laptop X", equipment_code="EQ-001", category="Computers", location="London", status="Active", description="Dell Latitude 7420"),
            Equipment(equipment_name="Forklift A", equipment_code="EQ-002", category="Vehicles", location="Warehouse A", status="Repair", description="Hydraulic leak"),
            Equipment(equipment_name="Router R1", equipment_code="EQ-003", category="Network", location="Data Center", status="Active", description="Core router"),
        ]
        db.session.add_all(samples)

    db.session.commit()

