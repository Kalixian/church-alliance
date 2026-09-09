"""CRUD operations for galleries and pictures."""

from io import BytesIO
from uuid import UUID

import cloudinary
import cloudinary.uploader
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.db.gallery.models import Gallery, Picture

DEFAULT_GALLERY_NAME = "Default"


def _configure_cloudinary() -> None:
    """Configure Cloudinary from the application's settings."""
    if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )


def _upload_picture_to_cloudinary(image_bytes: bytes, file_name: str | None = None) -> tuple[str, str | None]:
    """Upload an image to Cloudinary and return the public URL and public ID."""
    _configure_cloudinary()
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise ValueError("Cloudinary credentials are not configured")

    upload_result = cloudinary.uploader.upload(
        BytesIO(image_bytes),
        public_id=file_name or None,
        resource_type="auto",
        unique_filename=True,
        overwrite=False,
    )
    url = str(upload_result.get("secure_url") or upload_result.get("url") or "")
    public_id = upload_result.get("public_id")
    return url, public_id


def _delete_picture_from_cloudinary(public_id: str | None) -> None:
    """Delete a Cloudinary-hosted image using its stored public ID."""
    if not public_id:
        return

    _configure_cloudinary()
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        return

    cloudinary.uploader.destroy(public_id, resource_type="image")


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


def delete_gallery(db: Session, gallery_id: UUID) -> bool:
    """Delete a gallery and all associated pictures."""
    gallery = get_gallery_by_id(db, gallery_id)
    if not gallery:
        return False

    pictures = list(gallery.pictures)
    for picture in pictures:
        _delete_picture_from_cloudinary(picture.cloudinary_public_id)

    db.delete(gallery)
    db.commit()
    return True


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
    image_bytes: bytes | None = None,
    file_name: str | None = None,
    url: str | None = None,
) -> Picture | None:
    """Create a picture in a gallery."""
    resolved_gallery_id = gallery_id
    if resolved_gallery_id is None:
        default_gallery = get_default_gallery(db)
        resolved_gallery_id = default_gallery.id

    gallery = get_gallery_by_id(db, resolved_gallery_id)
    if not gallery:
        return None

    resolved_url = url
    resolved_public_id = None
    if image_bytes is not None:
        upload_result = _upload_picture_to_cloudinary(image_bytes, file_name=file_name)
        if isinstance(upload_result, tuple):
            resolved_url, resolved_public_id = upload_result
        else:
            resolved_url = upload_result

    picture = Picture(
        caption=caption,
        url=resolved_url,
        cloudinary_public_id=resolved_public_id,
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
    url: str | None = None,
) -> Picture | None:
    """Update a picture."""
    picture = get_picture_by_id(db, picture_id)
    if not picture:
        return None

    if caption is not None:
        picture.caption = caption
    if url is not None:
        picture.url = url
    if gallery_id is not None:
        gallery = get_gallery_by_id(db, gallery_id)
        if not gallery:
            return None
        picture.gallery_id = gallery_id

    db.commit()
    db.refresh(picture)
    return picture


def delete_picture(db: Session, picture_id: UUID) -> bool:
    """Delete a picture."""
    picture = get_picture_by_id(db, picture_id)
    if not picture:
        return False

    _delete_picture_from_cloudinary(picture.cloudinary_public_id)
    db.delete(picture)
    db.commit()
    return True
