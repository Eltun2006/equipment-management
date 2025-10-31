import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # SQLite in /tmp for Vercel (writable filesystem)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:////tmp/data.db"
    )
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads - use /tmp in serverless
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOADED_EXCELS_DEST = os.getenv(
        "UPLOADS_DIR",
        "/tmp"
    )

    # CORS - allow all in serverless (handled by Vercel)
    CORS_ORIGINS = ["*"]

