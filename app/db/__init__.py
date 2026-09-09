"""Database initialization and utilities"""

from .database import engine, SessionLocal, get_db
from .user import User
from .certification import Certification, user_certifications
from .asset import Asset, user_assets
from .gallery import Gallery, Picture, create_default_gallery
from .article import Article
from .base import Base
from sqlalchemy import inspect, text


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    _migrate_user_profile_columns()
    _migrate_event_schedule_columns()
    _migrate_picture_storage_columns()
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


def _migrate_event_schedule_columns():
    """Add scheduling fields to databases created before all-day events were supported."""
    inspector = inspect(engine)
    if "events" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("events")}
    missing_columns = {}
    if "all_day" not in existing_columns:
        missing_columns["all_day"] = "BOOLEAN NOT NULL DEFAULT 0"
    if "certification_id" not in existing_columns:
        missing_columns["certification_id"] = "UUID"

    if missing_columns:
        with engine.begin() as connection:
            for column_name, column_type in missing_columns.items():
                connection.execute(text(f"ALTER TABLE events ADD COLUMN {column_name} {column_type}"))

def _migrate_picture_storage_columns():
    """Add Cloudinary fields to databases created before picture uploads were supported."""
    inspector = inspect(engine)
    if "pictures" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("pictures")}
    missing_columns = {
        "url": "VARCHAR(2048)",
        "cloudinary_public_id": "VARCHAR(2048)",
    }

    with engine.begin() as connection:
        for column_name, column_type in missing_columns.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE pictures ADD COLUMN {column_name} {column_type}"))


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
    "Article",
    "Base",
    "create_tables",
]


