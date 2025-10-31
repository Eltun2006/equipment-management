import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'app.sqlite3')}"
    )
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOADED_EXCELS_DEST = os.getenv(
        "UPLOADS_DIR",
        os.path.join(os.path.dirname(__file__), "uploads")
    )

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

class ProdConfig(Config):
    SQLALCHEMY_ECHO = False

class DevConfig(Config):
    SQLALCHEMY_ECHO = False

config_by_name = {
    "development": DevConfig,
    "production": ProdConfig,
    "default": DevConfig,
}


