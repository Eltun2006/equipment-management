import os
import pathlib
from typing import Optional


def normalize_database_url(url: str) -> str:
    """Normalize DATABASE_URL to a SQLAlchemy-compatible URI.
    - Convert postgres:// to postgresql+psycopg2://
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_sqlite_uri(default_path: Optional[str] = None) -> str:
    if not default_path:
        default_path = os.path.join(os.path.dirname(__file__), 'app.sqlite3')
    # Absolute path for SQLite
    sqlite_path = pathlib.Path(default_path).resolve()
    return f"sqlite:///{sqlite_path}"


def get_database_uri() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return normalize_database_url(env_url)
    return get_sqlite_uri()


def configure_database(app) -> None:
    # Set SQLAlchemy URI based on env; default SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    # Sensible engine options for prod Postgres
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})
