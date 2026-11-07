import jwt
from sqlalchemy import create_engine, inspect, text

from app.config import settings
from app.db.gallery.crud import create_gallery
from app.db.user import UserCreate, UserRole, create_user


def make_user(db_session, auth_id: str, role: UserRole):
    return create_user(db_session, UserCreate(auth_id=auth_id, email=f"{auth_id}@example.com", role=role))


def auth(user) -> dict[str, str]:
    token = jwt.encode(
        {"sub": user.auth_id, "email": user.email},
        settings.supabase_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


def create_article(client, author, title="Picnic news"):
    response = client.post(
        "/api/v1/articles",
        headers=auth(author),
        json={"title": title, "content": [{"type": "paragraph", "children": [{"text": "Body"}]}]},
    )
    assert response.status_code == 201
    return response.json()


def upload(client, user, image_storage, gallery_id, public_id, caption=None):
    version = 1
    return client.post(
        "/api/v1/pictures",
        headers=auth(user),
        json={
            "public_id": public_id,
            "version": version,
            "signature": image_storage.signature_for(public_id, version),
            "gallery_id": gallery_id,
            "caption": caption,
        },
    )


def setup_users(db_session):
    admin = make_user(db_session, "ag-admin", UserRole.ADMINISTRATOR)
    author = make_user(db_session, "ag-author", UserRole.COORDINATOR)
    coordinator = make_user(db_session, "ag-coordinator", UserRole.COORDINATOR)
    member = make_user(db_session, "ag-member", UserRole.MEMBER)
    return admin, author, coordinator, member


def ensure_gallery(client, user, article_id):
    return client.put(f"/api/v1/articles/{article_id}/gallery", headers=auth(user))


def test_author_gets_one_gallery_per_article(client, db_session):
    _, author, _, _ = setup_users(db_session)
    article = create_article(client, author)
    assert article["gallery_id"] is None

    first = ensure_gallery(client, author, article["id"])
    second = ensure_gallery(client, author, article["id"])

    assert first.status_code == 200
    assert first.json()["article_id"] == article["id"]
    assert second.json()["id"] == first.json()["id"]
    assert client.get(f"/api/v1/articles/{article['id']}").json()["gallery_id"] == first.json()["id"]


def test_only_author_or_administrator_can_create_article_gallery(client, db_session):
    admin, author, coordinator, member = setup_users(db_session)
    article = create_article(client, author)

    assert ensure_gallery(client, member, article["id"]).status_code == 403
    assert ensure_gallery(client, coordinator, article["id"]).status_code == 403
    assert ensure_gallery(client, admin, article["id"]).status_code == 200


def test_only_author_or_administrator_can_upload_to_article_gallery(client, db_session, image_storage):
    admin, author, coordinator, member = setup_users(db_session)
    article = create_article(client, author)
    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]

    author_upload = upload(client, author, image_storage, gallery_id, "church-alliance/pictures/a1", "First")
    admin_upload = upload(client, admin, image_storage, gallery_id, "church-alliance/pictures/a2")
    coordinator_upload = upload(client, coordinator, image_storage, gallery_id, "church-alliance/pictures/a3")
    member_upload = upload(client, member, image_storage, gallery_id, "church-alliance/pictures/a4")

    assert author_upload.status_code == 200
    assert admin_upload.status_code == 200
    assert coordinator_upload.status_code == 403
    assert member_upload.status_code == 403

    pictures = client.get(f"/api/v1/galleries/{gallery_id}/pictures").json()
    assert [picture["caption"] for picture in pictures] == ["First", None]


def test_only_author_or_administrator_can_edit_or_delete_article_photos(client, db_session, image_storage):
    admin, author, coordinator, _ = setup_users(db_session)
    article = create_article(client, author)
    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]
    picture_id = upload(client, admin, image_storage, gallery_id, "church-alliance/pictures/e1").json()["id"]

    coordinator_edit = client.patch(f"/api/v1/pictures/{picture_id}", headers=auth(coordinator), json={"caption": "x"})
    author_edit = client.patch(f"/api/v1/pictures/{picture_id}", headers=auth(author), json={"caption": "Group photo"})
    coordinator_delete = client.delete(f"/api/v1/pictures/{picture_id}", headers=auth(coordinator))
    author_delete = client.delete(f"/api/v1/pictures/{picture_id}", headers=auth(author))

    assert coordinator_edit.status_code == 403
    assert author_edit.status_code == 200
    assert author_edit.json()["caption"] == "Group photo"
    assert coordinator_delete.status_code == 403
    assert author_delete.status_code == 204
    assert image_storage.deleted == ["church-alliance/pictures/e1"]


def test_article_galleries_are_hidden_from_main_gallery(client, db_session, image_storage):
    admin, author, _, _ = setup_users(db_session)
    article = create_article(client, author)
    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]
    upload(client, author, image_storage, gallery_id, "church-alliance/pictures/news")
    upload(client, author, image_storage, None, "church-alliance/pictures/general")

    galleries = client.get("/api/v1/galleries").json()
    pictures_response = client.get("/api/v1/pictures")

    assert gallery_id not in {gallery["id"] for gallery in galleries}
    assert [p["cloudinary_public_id"] for p in pictures_response.json()] == ["church-alliance/pictures/general"]
    assert pictures_response.headers["X-Total-Count"] == "1"
    filtered = client.get("/api/v1/pictures", params={"gallery_id": gallery_id}).json()
    assert [p["cloudinary_public_id"] for p in filtered] == ["church-alliance/pictures/news"]


def test_article_gallery_cannot_be_managed_through_gallery_routes(client, db_session, image_storage):
    admin, author, _, _ = setup_users(db_session)
    article = create_article(client, author)
    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]
    other_gallery = create_gallery(db_session, "Picnic")
    picture_id = upload(client, author, image_storage, gallery_id, "church-alliance/pictures/m1").json()["id"]

    rename = client.patch(f"/api/v1/galleries/{gallery_id}", headers=auth(admin), json={"name": "Renamed"})
    delete = client.delete(f"/api/v1/galleries/{gallery_id}", headers=auth(admin))
    move = client.post(f"/api/v1/galleries/{gallery_id}/move/{other_gallery.id}", headers=auth(admin))
    move_picture = client.patch(
        f"/api/v1/pictures/{picture_id}", headers=auth(admin), json={"gallery_id": str(other_gallery.id)}
    )

    assert {rename.status_code, delete.status_code, move.status_code, move_picture.status_code} == {409}


def test_deleting_article_removes_its_gallery_and_images(client, db_session, image_storage):
    _, author, _, _ = setup_users(db_session)
    article = create_article(client, author)
    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]
    upload(client, author, image_storage, gallery_id, "church-alliance/pictures/d1")
    upload(client, author, image_storage, gallery_id, "church-alliance/pictures/d2")

    response = client.delete(f"/api/v1/articles/{article['id']}", headers=auth(author))

    assert response.status_code == 204
    assert client.get(f"/api/v1/galleries/{gallery_id}").status_code == 404
    assert client.get(f"/api/v1/galleries/{gallery_id}/pictures").json() == []
    assert sorted(image_storage.deleted) == ["church-alliance/pictures/d1", "church-alliance/pictures/d2"]


def test_migration_adds_article_column_to_old_galleries_table(monkeypatch):
    import app.db as db_module

    old_engine = create_engine("sqlite:///:memory:")
    with old_engine.begin() as connection:
        connection.execute(text("CREATE TABLE articles (id UUID PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE galleries (id UUID PRIMARY KEY, name VARCHAR(255) NOT NULL)"))
    monkeypatch.setattr(db_module, "engine", old_engine)

    db_module._migrate_gallery_article_column()
    db_module._migrate_gallery_article_column()  # safe to run twice

    inspector = inspect(old_engine)
    assert "article_id" in {column["name"] for column in inspector.get_columns("galleries")}
    assert any(index["unique"] and index["column_names"] == ["article_id"] for index in inspector.get_indexes("galleries"))


def test_article_cover_is_its_first_photo(client, db_session, image_storage):
    _, author, _, _ = setup_users(db_session)
    article = create_article(client, author)
    assert article["cover_url"] is None

    gallery_id = ensure_gallery(client, author, article["id"]).json()["id"]
    upload(client, author, image_storage, gallery_id, "church-alliance/pictures/cover-first")
    upload(client, author, image_storage, gallery_id, "church-alliance/pictures/cover-second")

    listed = client.get("/api/v1/articles", params={"limit": 3}).json()
    assert listed[0]["cover_url"] == "https://images.example.test/v1/church-alliance/pictures/cover-first"
