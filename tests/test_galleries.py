from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.db.gallery.models import Picture
from app.db.user import UserCreate, UserRole, create_user
from app.db.gallery.crud import create_default_gallery


def make_token(sub: str, email: str, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def make_user_token(db_session, auth_id: str, role: UserRole) -> str:
    email = f"{auth_id}@example.com"
    create_user(db_session, UserCreate(auth_id=auth_id, email=email, role=role))
    return make_token(auth_id, email, settings.supabase_jwt_secret)


def confirm_upload(client, token, image_storage, public_id, version=1234, **fields):
    return client.post(
        "/api/v1/pictures",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "public_id": public_id,
            "version": version,
            "signature": image_storage.signature_for(public_id, version),
            **fields,
        },
    )


def test_default_gallery_is_created(db_session):
    gallery = create_default_gallery(db_session)

    assert gallery.name == "Default"
    assert gallery.id is not None


def test_member_can_get_upload_signature(client, db_session):
    token = make_user_token(db_session, "signature-member", UserRole.MEMBER)

    response = client.post("/api/v1/pictures/upload-signature", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"upload_url": "https://upload.example.test", "fields": {"signature": "upload-signature"}}


def test_applicant_cannot_get_upload_signature(client, db_session):
    make_user_token(db_session, "first-user-is-admin", UserRole.ADMINISTRATOR)
    token = make_user_token(db_session, "signature-applicant", UserRole.APPLICANT)

    response = client.post("/api/v1/pictures/upload-signature", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Only confirmed users can add pictures"


def test_member_can_confirm_upload_into_default_gallery(client, db_session, image_storage):
    token = make_user_token(db_session, "member-picture-user", UserRole.MEMBER)

    response = confirm_upload(client, token, image_storage, "church-alliance/pictures/abc", caption="Hello world")

    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "Hello world"
    assert data["url"] == "https://images.example.test/v1234/church-alliance/pictures/abc"
    assert data["cloudinary_public_id"] == "church-alliance/pictures/abc"
    assert data["gallery_id"] is not None
    assert image_storage.confirmed == ["church-alliance/pictures/abc"]


def test_confirm_rejects_forged_signature(client, db_session, image_storage):
    token = make_user_token(db_session, "forging-member", UserRole.MEMBER)

    response = client.post(
        "/api/v1/pictures",
        headers={"Authorization": f"Bearer {token}"},
        json={"public_id": "church-alliance/pictures/abc", "version": 1, "signature": "forged"},
    )

    assert response.status_code == 400
    assert db_session.query(Picture).count() == 0
    assert image_storage.confirmed == []


def test_confirm_rejects_reused_upload(client, db_session, image_storage):
    token = make_user_token(db_session, "reusing-member", UserRole.MEMBER)
    assert confirm_upload(client, token, image_storage, "church-alliance/pictures/once").status_code == 200

    response = confirm_upload(client, token, image_storage, "church-alliance/pictures/once")

    assert response.status_code == 409
    assert db_session.query(Picture).count() == 1


def test_confirm_into_missing_gallery_leaves_upload_pending(client, db_session, image_storage):
    token = make_user_token(db_session, "missing-gallery-member", UserRole.MEMBER)

    response = confirm_upload(
        client, token, image_storage, "church-alliance/pictures/lost",
        gallery_id="00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404
    assert image_storage.confirmed == []
    assert image_storage.deleted == []


def test_failed_save_deletes_uploaded_image(client, db_session, image_storage, monkeypatch):
    token = make_user_token(db_session, "failed-save-member", UserRole.MEMBER)

    def failing_create_picture(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.services.pictures.create_picture", failing_create_picture)

    with pytest.raises(RuntimeError):
        confirm_upload(client, token, image_storage, "church-alliance/pictures/orphan")

    assert image_storage.deleted == ["church-alliance/pictures/orphan"]


def test_deleting_picture_removes_stored_image(client, db_session, image_storage):
    token = make_user_token(db_session, "picture-deleter", UserRole.MEMBER)
    picture_id = confirm_upload(client, token, image_storage, "church-alliance/pictures/gone").json()["id"]

    response = client.delete(f"/api/v1/pictures/{picture_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert db_session.query(Picture).count() == 0
    assert image_storage.deleted == ["church-alliance/pictures/gone"]


def test_picture_delete_succeeds_when_storage_delete_fails(client, db_session, image_storage):
    token = make_user_token(db_session, "storage-down-deleter", UserRole.MEMBER)
    picture_id = confirm_upload(client, token, image_storage, "church-alliance/pictures/stuck").json()["id"]
    image_storage.fail_deletes = True

    response = client.delete(f"/api/v1/pictures/{picture_id}", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    assert db_session.query(Picture).count() == 0


def test_deleting_gallery_removes_associated_pictures(client, db_session, image_storage):
    token = make_user_token(db_session, "gallery-admin", UserRole.ADMINISTRATOR)

    gallery_response = client.post(
        "/api/v1/galleries",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Archive"},
    )
    assert gallery_response.status_code == 200
    gallery_id = gallery_response.json()["id"]

    for name in ("first", "second"):
        picture_response = confirm_upload(
            client, token, image_storage, f"church-alliance/pictures/{name}", gallery_id=gallery_id
        )
        assert picture_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/galleries/{gallery_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    assert db_session.query(Picture).all() == []
    assert sorted(image_storage.deleted) == ["church-alliance/pictures/first", "church-alliance/pictures/second"]


def test_move_pictures_route_moves_all_pictures_between_galleries(client, db_session, image_storage):
    token = make_user_token(db_session, "gallery-mover", UserRole.COORDINATOR)

    source_response = client.post(
        "/api/v1/galleries",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Source Gallery"},
    )
    target_response = client.post(
        "/api/v1/galleries",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Target Gallery"},
    )
    assert source_response.status_code == 200
    assert target_response.status_code == 200

    source_id = source_response.json()["id"]
    target_id = target_response.json()["id"]

    picture_response = confirm_upload(
        client, token, image_storage, "church-alliance/pictures/moved", caption="Moved item", gallery_id=source_id
    )
    assert picture_response.status_code == 200

    move_response = client.post(
        f"/api/v1/galleries/{source_id}/move/{target_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert move_response.status_code == 200
    moved_pictures = move_response.json()
    assert len(moved_pictures) == 1
    assert moved_pictures[0]["gallery_id"] == target_id
