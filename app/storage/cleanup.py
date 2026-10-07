"""Delete direct uploads that were never confirmed as Pictures.

Run periodically (e.g. a daily cron): `uv run python -m app.storage.cleanup`
"""

import logging
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import SessionLocal
from app.db.gallery.crud import get_existing_public_ids
from app.storage.images import CloudinaryImageStorage

logger = logging.getLogger(__name__)


def purge_abandoned_uploads(db: Session, storage: CloudinaryImageStorage, older_than: timedelta) -> list[str]:
    stale = storage.find_stale_pending(older_than)
    # Confirmed uploads lose the pending tag before their Picture is saved, so this should be empty;
    # checking anyway guarantees cleanup never breaks a picture that is in use.
    referenced = get_existing_public_ids(db, stale)
    to_delete = [public_id for public_id in stale if public_id not in referenced]
    storage.delete(to_delete)
    return to_delete


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    try:
        deleted = purge_abandoned_uploads(
            db,
            CloudinaryImageStorage.from_settings(),
            timedelta(hours=settings.cloudinary_pending_upload_ttl_hours),
        )
    finally:
        db.close()
    logger.info("Deleted %d abandoned uploads", len(deleted))


if __name__ == "__main__":
    main()
