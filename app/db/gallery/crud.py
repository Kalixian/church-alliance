"""CRUD operations for galleries and pictures. Database only: image storage is handled in app/services/pictures.py."""

from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.gallery.models import Gallery, Picture

DEFAULT_GALLERY_NAME = "Default"


def create_gallery(db: Session, name: str) -> Gallery | None:
    """Create a gallery if the name is available."""
    if get_gallery_by_name(db, name):
        return None
    gallery = Gallery(name=name)
    db.add(gallery)
    db.commit()
    db.refresh(gallery)
    return gallery


def create_default_gallery(db: Session) -> Gallery:
    """Ensure the default gallery exists."""
    gallery = get_gallery_by_name(db, DEFAULT_GALLERY_NAME)
    if gallery:
        return gallery
    gallery = Gallery(name=DEFAULT_GALLERY_NAME)
    db.add(gallery)
    db.commit()
    db.refresh(gallery)
    return gallery


def get_gallery_by_id(db: Session, gallery_id: UUID) -> Gallery | None:
    """Retrieve a gallery by its ID."""
    return db.query(Gallery).filter(Gallery.id == gallery_id).first()


def get_gallery_by_name(db: Session, name: str) -> Gallery | None:
    """Retrieve a gallery by its name."""
    return db.query(Gallery).filter(Gallery.name == name).first()


def get_default_gallery(db: Session) -> Gallery:
    """Return the default gallery, creating it if needed."""
    return create_default_gallery(db)


def get_all_galleries(db: Session, skip: int = 0, limit: int = 100) -> list[Gallery]:
    """Get all galleries."""
    return db.query(Gallery).offset(skip).limit(limit).all()


def update_gallery(db: Session, gallery_id: UUID, name: str | None = None) -> Gallery | None:
    """Update a gallery."""
    gallery = get_gallery_by_id(db, gallery_id)
    if not gallery:
        return None
    if name is not None:
        gallery.name = name
    db.commit()
    db.refresh(gallery)
    return gallery


def delete_gallery(db: Session, gallery_id: UUID) -> list[str] | None:
    """Delete a gallery and all its pictures. Returns the deleted pictures' storage IDs, or None if not found."""
    gallery = get_gallery_by_id(db, gallery_id)
    if not gallery:
        return None

    public_ids = [picture.cloudinary_public_id for picture in gallery.pictures if picture.cloudinary_public_id]
    db.delete(gallery)
    db.commit()
    return public_ids


def move_pictures_between_galleries(
    db: Session,
    source_gallery_id: UUID,
    target_gallery_id: UUID,
) -> list[Picture] | None:
    """Move all pictures from one gallery to another."""
    source_gallery = get_gallery_by_id(db, source_gallery_id)
    target_gallery = get_gallery_by_id(db, target_gallery_id)
    if not source_gallery or not target_gallery:
        return None

    pictures = get_pictures_by_gallery(db, source_gallery_id)
    for picture in pictures:
        picture.gallery_id = target_gallery_id

    db.commit()
    return pictures


def create_picture(
    db: Session,
    caption: str | None,
    gallery_id: UUID | None,
    uploaded_by_id: UUID,
    url: str,
    cloudinary_public_id: str | None = None,
) -> Picture | None:
    """Create a picture in a gallery."""
    resolved_gallery_id = gallery_id
    if resolved_gallery_id is None:
        default_gallery = get_default_gallery(db)
        resolved_gallery_id = default_gallery.id

    gallery = get_gallery_by_id(db, resolved_gallery_id)
    if not gallery:
        return None

    picture = Picture(
        caption=caption,
        url=url,
        cloudinary_public_id=cloudinary_public_id,
        gallery_id=resolved_gallery_id,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(picture)
    db.commit()
    db.refresh(picture)
    return picture


def get_picture_by_id(db: Session, picture_id: UUID) -> Picture | None:
    """Retrieve a picture by its ID."""
    return db.query(Picture).filter(Picture.id == picture_id).first()


def get_picture_by_public_id(db: Session, public_id: str) -> Picture | None:
    """Retrieve a picture by its storage public ID."""
    return db.query(Picture).filter(Picture.cloudinary_public_id == public_id).first()


def get_existing_public_ids(db: Session, public_ids: list[str]) -> set[str]:
    """Return which of the given storage public IDs are referenced by a picture."""
    if not public_ids:
        return set()
    rows = db.query(Picture.cloudinary_public_id).filter(Picture.cloudinary_public_id.in_(public_ids)).all()
    return {row[0] for row in rows}


def get_all_pictures(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    gallery_id: UUID | None = None,
) -> list[Picture]:
    """Get pictures filtered by caption/gallery, newest first."""
    query = db.query(Picture)
    if search:
        query = query.filter(Picture.caption.ilike(f"%{search}%"))
    if gallery_id:
        query = query.filter(Picture.gallery_id == gallery_id)
    return query.order_by(Picture.uploaded_at.desc(), Picture.id.desc()).offset(skip).limit(limit).all()


def count_pictures(
    db: Session,
    search: str | None = None,
    gallery_id: UUID | None = None,
) -> int:
    """Count pictures using the same filters as the paginated list."""
    query = db.query(func.count(Picture.id))
    if search:
        query = query.filter(Picture.caption.ilike(f"%{search}%"))
    if gallery_id:
        query = query.filter(Picture.gallery_id == gallery_id)
    return query.scalar() or 0


def get_pictures_by_gallery(db: Session, gallery_id: UUID) -> list[Picture]:
    """Get all pictures for a gallery."""
    return db.query(Picture).filter(Picture.gallery_id == gallery_id).all()


def update_picture(
    db: Session,
    picture_id: UUID,
    caption: str | None = None,
    gallery_id: UUID | None = None,
) -> Picture | None:
    """Update a picture's caption or gallery."""
    picture = get_picture_by_id(db, picture_id)
    if not picture:
        return None

    if caption is not None:
        picture.caption = caption
    if gallery_id is not None:
        gallery = get_gallery_by_id(db, gallery_id)
        if not gallery:
            return None
        picture.gallery_id = gallery_id

    db.commit()
    db.refresh(picture)
    return picture


def delete_picture(db: Session, picture_id: UUID) -> list[str] | None:
    """Delete a picture. Returns its storage IDs (empty if it had none), or None if not found."""
    picture = get_picture_by_id(db, picture_id)
    if not picture:
        return None

    public_ids = [picture.cloudinary_public_id] if picture.cloudinary_public_id else []
    db.delete(picture)
    db.commit()
    return public_ids
