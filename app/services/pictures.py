"""Keeps Picture rows and stored images consistent.

Failure ordering is deliberate: when the two can't both succeed, prefer an orphaned image in storage
(costs a little space, removed by cleanup) over a Picture whose image no longer exists.
"""

import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.db.gallery.crud import (
    create_picture,
    delete_gallery,
    delete_picture,
    get_default_gallery,
    get_gallery_by_id,
    get_picture_by_public_id,
)
from app.db.gallery.models import Picture
from app.storage import ImageStorage, StorageUnavailableError

logger = logging.getLogger(__name__)


class DuplicateUploadError(ValueError):
    """The upload has already been saved as a Picture."""


def confirm_upload(
    db: Session,
    storage: ImageStorage,
    *,
    public_id: str,
    version: int,
    signature: str,
    caption: str | None,
    gallery_id: UUID | None,
    uploaded_by_id: UUID,
) -> Picture | None:
    """Save a Picture for a verified direct upload. Returns None if the gallery doesn't exist.

    Raises UploadVerificationError, DuplicateUploadError or StorageUnavailableError.
    """
    image = storage.verify_upload(public_id, version, signature)
    if get_picture_by_public_id(db, image.public_id):
        raise DuplicateUploadError("This upload has already been saved")

    resolved_gallery_id = gallery_id or get_default_gallery(db).id
    if not get_gallery_by_id(db, resolved_gallery_id):
        return None  # The image stays tagged pending, so cleanup removes it.

    storage.confirm(image.public_id)
    try:
        return create_picture(
            db,
            caption=caption,
            gallery_id=resolved_gallery_id,
            uploaded_by_id=uploaded_by_id,
            url=image.url,
            cloudinary_public_id=image.public_id,
        )
    except Exception:
        db.rollback()
        _delete_images(storage, [image.public_id])
        raise


def remove_picture(
    db: Session,
    storage: ImageStorage,
    background_tasks: BackgroundTasks,
    picture_id: UUID,
) -> bool:
    """Delete a Picture, then its image after the response is sent. Returns False if not found."""
    public_ids = delete_picture(db, picture_id)
    if public_ids is None:
        return False
    background_tasks.add_task(_delete_images, storage, public_ids)
    return True


def remove_gallery(
    db: Session,
    storage: ImageStorage,
    background_tasks: BackgroundTasks,
    gallery_id: UUID,
) -> bool:
    """Delete a gallery and its Pictures, then their images after the response is sent."""
    public_ids = delete_gallery(db, gallery_id)
    if public_ids is None:
        return False
    background_tasks.add_task(_delete_images, storage, public_ids)
    return True


def _delete_images(storage: ImageStorage, public_ids: list[str]) -> None:
    try:
        storage.delete(public_ids)
    except StorageUnavailableError:
        logger.exception("Failed to delete images from storage: %s", public_ids)
