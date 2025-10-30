import os
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

from .config import config_by_name
from .models import db, User, Equipment, Comment
from .auth import auth_bp
from .equipment import equipment_bp
from .comments import comments_bp
from .socketio_events import init_socketio, register_socket_handlers, broadcast_new_comment, broadcast_comment_deleted
from .utils import hash_password

socketio: Optional[SocketIO] = None


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    cfg = config_by_name.get(config_name or os.getenv("FLASK_ENV", "default"))
    app.config.from_object(cfg)

    # Init extensions
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}})

    # Uploads directory (optional): keep directory for potential storage, but use request.files directly
    if not os.path.isdir(app.config["UPLOADED_EXCELS_DEST"]):
        os.makedirs(app.config["UPLOADED_EXCELS_DEST"], exist_ok=True)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(comments_bp)

    # DB create
    with app.app_context():
        db.create_all()
        # Lightweight migration: ensure 'extra' column exists on equipment
        try:
            insp = db.inspect(db.engine)
            cols = {c['name'] for c in insp.get_columns('equipment')}
            if 'extra' not in cols:
                with db.engine.begin() as conn:
                    conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra JSON")
        except Exception:
            # Best-effort; on SQLite older versions JSON resolves to TEXT
            try:
                with db.engine.begin() as conn:
                    conn.exec_driver_sql("ALTER TABLE equipment ADD COLUMN extra TEXT")
            except Exception:
                pass
        seed_data()

    # SocketIO
    global socketio
    socketio = SocketIO(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", ["*"]), async_mode="eventlet")
    init_socketio(socketio)
    register_socket_handlers(socketio)

    # Hook comment create/delete to broadcast
    @app.after_request
    def after_request(response):
        return response

    # Health check
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    return app


def seed_data():
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


if __name__ == "__main__":
    app = create_app()
    # Use port from env or default 5000
    port = int(os.getenv("PORT", 5000))
    # Eventlet is installed; SocketIO will pick it. Set allow_unsafe_werkzeug for local dev if necessary.
    print(f"Server starting on http://localhost:{port} (Socket.IO enabled)")
    socketio.run(app, host="0.0.0.0", port=port)
