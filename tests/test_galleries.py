from datetime import datetime, timedelta, timezone

from jose import jwt

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


def test_default_gallery_is_created(db_session):
    gallery = create_default_gallery(db_session)

    assert gallery.name == "Default"
    assert gallery.id is not None


def test_member_can_create_picture_in_default_gallery(client, db_session, monkeypatch):
    create_user(
        db_session,
        UserCreate(
            auth_id="member-picture-user",
            email="member-picture@example.com",
            role=UserRole.MEMBER,
        ),
    )
    token = make_token("member-picture-user", "member-picture@example.com", settings.supabase_jwt_secret)

    monkeypatch.setattr(
        "app.db.gallery.crud._upload_picture_to_cloudinary",
        lambda image_bytes, file_name=None: "https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg",
    )

    response = client.post(
        "/api/v1/pictures",
        headers={"Authorization": f"Bearer {token}"},
        data={"caption": "Hello world"},
        files={"image": ("sample.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "Hello world"
    assert data["url"] == "https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg"
    assert data["uploaded_by_id"] is not None
    assert data["gallery_id"] is not None


def test_deleting_gallery_removes_associated_pictures(client, db_session, monkeypatch):
    create_user(
        db_session,
        UserCreate(
            auth_id="gallery-admin",
            email="gallery-admin@example.com",
            role=UserRole.ADMINISTRATOR,
        ),
    )
    token = make_token("gallery-admin", "gallery-admin@example.com", settings.supabase_jwt_secret)

    monkeypatch.setattr(
        "app.db.gallery.crud._upload_picture_to_cloudinary",
        lambda image_bytes, file_name=None: "https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg",
    )
    monkeypatch.setattr("app.db.gallery.crud._delete_picture_from_cloudinary", lambda url: None)

    gallery_response = client.post(
        "/api/v1/galleries",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Archive"},
    )
    assert gallery_response.status_code == 200
    gallery_id = gallery_response.json()["id"]

    picture_response = client.post(
        "/api/v1/pictures",
        headers={"Authorization": f"Bearer {token}"},
        data={"caption": "Archive item", "gallery_id": gallery_id},
        files={"image": ("archive.png", b"fake-image-bytes", "image/png")},
    )
    assert picture_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/galleries/{gallery_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    remaining_pictures = db_session.query(Picture).all()
    assert remaining_pictures == []


def test_move_pictures_route_moves_all_pictures_between_galleries(client, db_session, monkeypatch):
    create_user(
        db_session,
        UserCreate(
            auth_id="gallery-mover",
            email="gallery-mover@example.com",
            role=UserRole.ORGANIZER,
        ),
    )
    token = make_token("gallery-mover", "gallery-mover@example.com", settings.supabase_jwt_secret)

    monkeypatch.setattr(
        "app.db.gallery.crud._upload_picture_to_cloudinary",
        lambda image_bytes, file_name=None: "https://res.cloudinary.com/demo/image/upload/v1234/sample.jpg",
    )

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

    picture_response = client.post(
        "/api/v1/pictures",
        headers={"Authorization": f"Bearer {token}"},
        data={"caption": "Moved item", "gallery_id": source_id},
        files={"image": ("moved.png", b"fake-image-bytes", "image/png")},
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
