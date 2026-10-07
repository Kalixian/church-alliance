import jwt

from app.config import settings
from app.db.user import UserCreate, UserRole, create_user


def make_token(user):
    return jwt.encode(
        {"sub": user.auth_id, "email": user.email},
        settings.supabase_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def slate_content():
    return [
        {"type": "heading-one", "children": [{"text": "First line", "bold": True}]},
        {"type": "paragraph", "children": [{"text": "Second line"}]},
        {"type": "paragraph", "children": [{"text": "Third line"}]},
        {"type": "paragraph", "children": [{"text": "Fourth line"}]},
    ]


def test_article_defaults_summary_and_returns_creator(client, db_session):
    creator = create_user(
        db_session,
        UserCreate(auth_id="article-creator", email="article-creator@example.com", role=UserRole.MEMBER),
    )

    response = client.post(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {make_token(creator)}"},
        json={"title": "Response update", "content": slate_content()},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["summary"] == "First line\nSecond line\nThird line"
    assert data["creator_id"] == str(creator.id)
    assert data["creator"]["id"] == str(creator.id)
    assert data["content"][0]["children"][0]["bold"] is True


def test_article_rejects_dangerous_slate_link(client, db_session):
    creator = create_user(
        db_session,
        UserCreate(auth_id="unsafe-article-creator", email="unsafe-article@example.com", role=UserRole.MEMBER),
    )

    response = client.post(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {make_token(creator)}"},
        json={
            "title": "Unsafe article",
            "content": [{"type": "link", "url": "javascript:alert(1)", "children": [{"text": "Click"}]}],
        },
    )

    assert response.status_code == 422


def test_only_creator_or_manager_can_update_and_delete_article(client, db_session):
    creator = create_user(
        db_session,
        UserCreate(auth_id="owned-article-creator", email="owned-article@example.com", role=UserRole.MEMBER),
    )
    other_member = create_user(
        db_session,
        UserCreate(auth_id="other-article-member", email="other-article@example.com", role=UserRole.MEMBER),
    )
    administrator = create_user(
        db_session,
        UserCreate(auth_id="article-administrator", email="article-admin@example.com", role=UserRole.ADMINISTRATOR),
    )

    article_response = client.post(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {make_token(creator)}"},
        json={"title": "Owned article", "content": slate_content(), "summary": "Custom summary"},
    )
    article_id = article_response.json()["id"]

    denied_response = client.patch(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {make_token(other_member)}"},
        json={"title": "Changed by stranger"},
    )
    owner_response = client.patch(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {make_token(creator)}"},
        json={"content": [{"type": "paragraph", "children": [{"text": "New body"}]}]},
    )
    admin_delete_response = client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {make_token(administrator)}"},
    )

    assert denied_response.status_code == 403
    assert owner_response.status_code == 200
    assert owner_response.json()["summary"] == "New body"
    assert admin_delete_response.status_code == 204
