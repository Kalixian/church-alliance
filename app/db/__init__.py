"""Database initialization and utilities"""

from .database import engine, SessionLocal, get_db
from .user import User
from .certification import Certification, user_certifications
from .asset import Asset, user_assets
from .gallery import Gallery, Picture, create_default_gallery
from .base import Base
from sqlalchemy import inspect, text


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    _migrate_user_profile_columns()
    db = SessionLocal()
    try:
        create_default_gallery(db)
    finally:
        db.close()


def _migrate_user_profile_columns():
    """Add nullable user profile columns to databases created by older versions."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    missing_columns = {
        "first_name": "VARCHAR(255)",
        "last_name": "VARCHAR(255)",
    }

    with engine.begin() as connection:
        for column_name, column_type in missing_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))


__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "User",
    "Certification",
    "Asset",
    "user_certifications",
    "user_assets",
    "Gallery",
    "Picture",
    "Base",
    "create_tables",
]


