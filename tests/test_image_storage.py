"""CloudinaryImageStorage against Cloudinary's documented signing scheme, with the network stubbed."""

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.db.gallery.crud import create_default_gallery, create_picture
from app.db.user import UserCreate, create_user
from app.storage import CloudinaryImageStorage, StorageUnavailableError, UploadVerificationError
from app.storage.cleanup import purge_abandoned_uploads

SECRET = "test-api-secret"


@pytest.fixture()
def storage():
    return CloudinaryImageStorage("demo-cloud", "test-api-key", SECRET, "church-alliance/pictures")


def cloudinary_sign(params: dict) -> str:
    """Cloudinary's scheme: sorted key=value pairs joined by '&', secret appended, SHA-1."""
    to_sign = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.sha1((to_sign + SECRET).encode()).hexdigest()


def test_upload_signature_signs_folder_tag_and_formats(storage):
    signature = storage.create_upload_signature()
    fields = signature.fields

    assert signature.upload_url == "https://api.cloudinary.com/v1_1/demo-cloud/image/upload"
    assert fields["folder"] == "church-alliance/pictures"
    assert fields["tags"] == "pending"
    assert fields["api_key"] == "test-api-key"
    signed_params = {key: fields[key] for key in ("timestamp", "folder", "tags", "allowed_formats")}
    assert fields["signature"] == cloudinary_sign(signed_params)


def test_verify_upload_accepts_cloudinary_response_signature(storage):
    public_id = "church-alliance/pictures/photo1"
    signature = cloudinary_sign({"public_id": public_id, "version": 1700000000})

    image = storage.verify_upload(public_id, 1700000000, signature)

    assert image.public_id == public_id
    assert image.url == "https://res.cloudinary.com/demo-cloud/image/upload/v1700000000/church-alliance/pictures/photo1"


def test_verify_upload_rejects_tampered_version(storage):
    public_id = "church-alliance/pictures/photo1"
    signature = cloudinary_sign({"public_id": public_id, "version": 1700000000})

    with pytest.raises(UploadVerificationError):
        storage.verify_upload(public_id, 1700000001, signature)


def test_verify_upload_rejects_other_folders(storage):
    public_id = "someone-else/photo1"
    signature = cloudinary_sign({"public_id": public_id, "version": 1})

    with pytest.raises(UploadVerificationError):
        storage.verify_upload(public_id, 1, signature)


def test_unconfigured_storage_is_unavailable():
    storage = CloudinaryImageStorage(None, None, None, "church-alliance/pictures")

    with pytest.raises(StorageUnavailableError):
        storage.create_upload_signature()
    storage.delete([])  # nothing to delete never needs credentials


def test_delete_batches_requests(storage, monkeypatch):
    calls = []
    monkeypatch.setattr("cloudinary.api.delete_resources", lambda ids, **options: calls.append(ids))

    storage.delete([f"church-alliance/pictures/{index}" for index in range(250)])

    assert [len(batch) for batch in calls] == [100, 100, 50]


def test_purge_removes_only_old_unreferenced_pending_uploads(storage, db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pages = {
        None: {
            "resources": [
                {"public_id": "church-alliance/pictures/abandoned", "created_at": old},
                {"public_id": "church-alliance/pictures/in-progress", "created_at": recent},
            ],
            "next_cursor": "page-2",
        },
        "page-2": {"resources": [{"public_id": "church-alliance/pictures/saved", "created_at": old}]},
    }
    monkeypatch.setattr(
        "cloudinary.api.resources_by_tag",
        lambda tag, **options: pages[options.get("next_cursor")],
    )
    deleted = []
    monkeypatch.setattr("cloudinary.api.delete_resources", lambda ids, **options: deleted.extend(ids))

    user = create_user(db_session, UserCreate(auth_id=f"purge-{uuid4()}", email=f"purge-{uuid4()}@example.com"))
    create_picture(
        db_session,
        caption=None,
        gallery_id=create_default_gallery(db_session).id,
        uploaded_by_id=user.id,
        url="https://res.cloudinary.com/demo-cloud/image/upload/v1/church-alliance/pictures/saved",
        cloudinary_public_id="church-alliance/pictures/saved",
    )

    purged = purge_abandoned_uploads(db_session, storage, timedelta(hours=24))

    assert purged == ["church-alliance/pictures/abandoned"]
    assert deleted == ["church-alliance/pictures/abandoned"]
