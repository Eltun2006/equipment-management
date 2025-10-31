"""Shared Flask app factory for Vercel serverless functions"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib.database import db, get_app_config, init_db

_app = None

def get_app():
    """Get or create Flask app instance (singleton for serverless)"""
    global _app
    if _app is None:
        _app = Flask(__name__)
        config = get_app_config()
        _app.config.update(config)
        
        # Initialize extensions
        db.init_app(_app)
        JWTManager(_app)
        CORS(_app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
        
        # Initialize database (creates tables and seeds)
        with _app.app_context():
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
            
            # Seed data only if tables are empty
            try:
                from lib.models import User, Equipment
                from lib.utils import hash_password
                
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
                # Don't fail if seeding fails
    
    return _app

