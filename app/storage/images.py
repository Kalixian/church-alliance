"""Image storage backed by Cloudinary signed direct uploads.

Upload flow: the API hands the browser a signed upload request (`create_upload_signature`), the browser
uploads straight to Cloudinary, and the API then checks Cloudinary's signed response (`verify_upload`)
before saving a Picture. Uploads carry a "pending" tag until `confirm` removes it, so abandoned uploads
can be found and purged later (see `app/storage/cleanup.py`).
"""

import hmac
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Protocol

import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils

from app.config import settings

logger = logging.getLogger(__name__)

PENDING_TAG = "pending"
ALLOWED_FORMATS = "jpg,jpeg,png,gif,webp,heic"
_DELETE_BATCH_SIZE = 100  # Cloudinary's limit per delete_resources call


class StorageUnavailableError(RuntimeError):
    """Storage is not configured or Cloudinary could not be reached."""


class UploadVerificationError(ValueError):
    """An upload response did not come from a signed upload to our folder."""


@dataclass(frozen=True)
class StoredImage:
    public_id: str
    url: str


@dataclass(frozen=True)
class UploadSignature:
    upload_url: str
    fields: dict[str, str]  # sent verbatim as form fields alongside the file


class ImageStorage(Protocol):
    def create_upload_signature(self) -> UploadSignature: ...

    def verify_upload(self, public_id: str, version: int, signature: str) -> StoredImage: ...

    def confirm(self, public_id: str) -> None: ...

    def delete(self, public_ids: Iterable[str]) -> None: ...


class CloudinaryImageStorage:
    def __init__(
        self,
        cloud_name: str | None,
        api_key: str | None,
        api_secret: str | None,
        folder: str,
    ):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.folder = folder.strip("/")

    @classmethod
    def from_settings(cls) -> "CloudinaryImageStorage":
        return cls(
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
            settings.cloudinary_upload_folder,
        )

    def _credentials(self) -> dict[str, str]:
        if not (self.cloud_name and self.api_key and self.api_secret):
            raise StorageUnavailableError("Cloudinary credentials are not configured")
        return {"cloud_name": self.cloud_name, "api_key": self.api_key, "api_secret": self.api_secret}

    def create_upload_signature(self) -> UploadSignature:
        credentials = self._credentials()
        params = {
            "timestamp": str(int(time.time())),
            "folder": self.folder,
            "tags": PENDING_TAG,
            "allowed_formats": ALLOWED_FORMATS,
        }
        signature = cloudinary.utils.api_sign_request(params, credentials["api_secret"])
        upload_url = cloudinary.utils.cloudinary_api_url(
            "upload", resource_type="image", cloud_name=credentials["cloud_name"]
        )
        return UploadSignature(
            upload_url=upload_url,
            fields={**params, "api_key": credentials["api_key"], "signature": signature},
        )

    def verify_upload(self, public_id: str, version: int, signature: str) -> StoredImage:
        credentials = self._credentials()
        if not public_id.startswith(f"{self.folder}/"):
            raise UploadVerificationError("Upload is not in the expected folder")

        # Cloudinary signs upload responses with signature version 1 over public_id and version.
        expected = cloudinary.utils.api_sign_request(
            {"public_id": public_id, "version": version},
            credentials["api_secret"],
            signature_version=1,
        )
        if not hmac.compare_digest(expected, signature):
            raise UploadVerificationError("Upload signature is invalid")

        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            version=version,
            resource_type="image",
            type="upload",
            secure=True,
            cloud_name=credentials["cloud_name"],
        )
        return StoredImage(public_id=public_id, url=url)

    def confirm(self, public_id: str) -> None:
        try:
            cloudinary.uploader.remove_tag(PENDING_TAG, [public_id], **self._credentials())
        except cloudinary.exceptions.Error as exc:
            raise StorageUnavailableError("Could not confirm the upload with Cloudinary") from exc

    def delete(self, public_ids: Iterable[str]) -> None:
        ids = [public_id for public_id in public_ids if public_id]
        if not ids:
            return
        credentials = self._credentials()
        try:
            for start in range(0, len(ids), _DELETE_BATCH_SIZE):
                cloudinary.api.delete_resources(
                    ids[start:start + _DELETE_BATCH_SIZE],
                    resource_type="image",
                    type="upload",
                    **credentials,
                )
        except cloudinary.exceptions.Error as exc:
            raise StorageUnavailableError("Could not delete images from Cloudinary") from exc

    def find_stale_pending(self, older_than: timedelta) -> list[str]:
        """Public IDs still tagged pending that were uploaded before `older_than` ago."""
        credentials = self._credentials()
        cutoff = datetime.now(timezone.utc) - older_than
        stale: list[str] = []
        next_cursor = None
        while True:
            options = {"resource_type": "image", "max_results": 500, **credentials}
            if next_cursor:
                options["next_cursor"] = next_cursor
            result = cloudinary.api.resources_by_tag(PENDING_TAG, **options)
            for resource in result.get("resources", []):
                if datetime.fromisoformat(resource["created_at"]) < cutoff:
                    stale.append(resource["public_id"])
            next_cursor = result.get("next_cursor")
            if not next_cursor:
                return stale


def get_image_storage() -> ImageStorage:
    """FastAPI dependency; tests override it with an in-memory fake."""
    return CloudinaryImageStorage.from_settings()
