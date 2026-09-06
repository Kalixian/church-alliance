"""CRUD operations for assets."""

from sqlalchemy.orm import Session
from app.db.asset.models import Asset, user_assets
from app.db.user.models import User
from uuid import UUID
from sqlalchemy import select


def create_asset(db: Session, name: str, description: str | None = None) -> Asset:
    """Create a new asset."""
    asset = Asset(name=name, description=description)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def get_asset_by_id(db: Session, asset_id: UUID) -> Asset | None:
    """Get an asset by its ID."""
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_asset_by_name(db: Session, name: str) -> Asset | None:
    """Get an asset by its name."""
    return db.query(Asset).filter(Asset.name == name).first()


def get_all_assets(db: Session, skip: int = 0, limit: int = 100) -> list[Asset]:
    """Get all assets."""
    return db.query(Asset).offset(skip).limit(limit).all()


def update_asset(db: Session, asset_id: UUID, name: str | None = None, description: str | None = None) -> Asset | None:
    """Update an existing asset."""
    asset = get_asset_by_id(db, asset_id)
    if not asset:
        return None
    if name is not None:
        asset.name = name
    if description is not None:
        asset.description = description
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: UUID) -> bool:
    """Delete an asset."""
    asset = get_asset_by_id(db, asset_id)
    if not asset:
        return False
    db.delete(asset)
    db.commit()
    return True


def assign_asset_to_user(
    db: Session,
    user_id: UUID,
    asset_id: UUID,
    quantity: str | None = None,
    notes: str | None = None,
    available: bool | None = True,
) -> bool:
    """Assign an asset to a user with optional metadata."""
    user = db.query(User).filter(User.id == user_id).first()
    asset = get_asset_by_id(db, asset_id)
    if not user or not asset:
        return False

    exists = db.execute(
        select(user_assets).where(
            user_assets.c.user_id == user_id,
            user_assets.c.asset_id == asset_id,
        )
    ).first()
    if exists:
        return True

    db.execute(
        user_assets.insert().values(
            user_id=user_id,
            asset_id=asset_id,
            quantity=quantity,
            notes=notes,
            available=available,
        )
    )
    db.commit()
    return True


def remove_asset_from_user(db: Session, user_id: UUID, asset_id: UUID) -> bool:
    """Remove an asset assignment from a user."""
    res = db.execute(
        user_assets.delete().where(
            user_assets.c.user_id == user_id,
            user_assets.c.asset_id == asset_id,
        )
    )
    db.commit()
    return (res.rowcount or 0) > 0


def get_users_by_asset(
    db: Session,
    asset_id: UUID | None = None,
    asset_name: str | None = None,
) -> list[User]:
    """Get all users associated with a specific asset."""
    query = db.query(User).join(user_assets).join(Asset)
    if asset_id is not None:
        query = query.filter(Asset.id == asset_id)
    if asset_name is not None:
        query = query.filter(Asset.name == asset_name)
    return query.distinct().all()
