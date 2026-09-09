from datetime import datetime, timedelta, timezone
from jose import jwt

from app.config import settings
from app.db.user import create_user, get_user_by_auth_id, update_user, UserCreate, UserRole, UserUpdate


def make_token(sub: str, email: str, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def test_me_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_me_creates_user_and_returns_profile(client):
    token = make_token("test-user-1", "test1@example.com", settings.supabase_jwt_secret)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["auth_id"] == "test-user-1"
    assert user_data["email"] == "test1@example.com"


def test_sync_user_returns_same_profile(client):
    token = make_token("test-user-2", "test2@example.com", settings.supabase_jwt_secret)
    response = client.post(
        "/api/v1/auth/sync-user",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["auth_id"] == "test-user-2"
    assert user_data["email"] == "test2@example.com"


def test_me_updates_user_email_when_token_email_changes(client, db_session):
    create_user(
        db_session,
        UserCreate(
            auth_id="user-email-update",
            email="old@example.com",
            role=UserRole.APPLICANT,
        ),
    )

    token = make_token("user-email-update", "new@example.com", settings.supabase_jwt_secret)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"

    updated_user = db_session.query(
        __import__("app.db.user", fromlist=["User"]).User
    ).filter_by(auth_id="user-email-update").one()
    assert updated_user.email == "new@example.com"


def test_admin_route_denies_non_admin(client, db_session):
    create_user(
        db_session,
        UserCreate(
            auth_id="existing-admin",
            email="existing-admin@example.com",
        ),
    )
    token = make_token("non-admin", "user@example.com", settings.supabase_jwt_secret)
    response = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_route_allows_admin(client, db_session):
    create_user(
        db_session,
        UserCreate(
            auth_id="admin-user",
            email="admin@example.com",
            role=UserRole.ADMINISTRATOR,
        ),
    )
    token = make_token("admin-user", "admin@example.com", settings.supabase_jwt_secret)
    response = client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_id"] == "admin-user"
    assert data["role"] == UserRole.ADMINISTRATOR.value


def test_admin_can_update_user_role(client, db_session):
    admin = create_user(
        db_session,
        UserCreate(
            auth_id="role-admin",
            email="role-admin@example.com",
        ),
    )
    member = create_user(
        db_session,
        UserCreate(
            auth_id="role-member",
            email="role-member@example.com",
        ),
    )
    admin_token = make_token("role-admin", admin.email, settings.supabase_jwt_secret)

    response = client.patch(
        f"/api/v1/users/{member.id}/role",
        params={"new_role": UserRole.COORDINATOR.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == UserRole.COORDINATOR.value


def test_coordinator_cannot_update_user_role(client, db_session):
    coordinator = create_user(
        db_session,
        UserCreate(
            auth_id="role-coordinator",
            email="role-coordinator@example.com",
        ),
    )
    member = create_user(
        db_session,
        UserCreate(
            auth_id="role-member-denied",
            email="role-member-denied@example.com",
        ),
    )
    update_user(db_session, coordinator.id, UserUpdate(role=UserRole.COORDINATOR))
    coordinator_token = make_token("role-coordinator", coordinator.email, settings.supabase_jwt_secret)

    response = client.patch(
        f"/api/v1/users/{member.id}/role",
        params={"new_role": UserRole.MEMBER.value},
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )

    assert response.status_code == 403


def test_admin_cannot_update_own_role(client, db_session):
    admin = create_user(
        db_session,
        UserCreate(
            auth_id="self-role-admin",
            email="self-role-admin@example.com",
        ),
    )
    admin_token = make_token("self-role-admin", admin.email, settings.supabase_jwt_secret)

    response = client.patch(
        f"/api/v1/users/{admin.id}/role",
        params={"new_role": UserRole.MEMBER.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Administrators cannot change their own role"


def test_admin_can_delete_another_user(client, db_session):
    admin = create_user(
        db_session,
        UserCreate(
            auth_id="delete-admin",
            email="delete-admin@example.com",
        ),
    )
    member = create_user(
        db_session,
        UserCreate(
            auth_id="delete-member",
            email="delete-member@example.com",
        ),
    )
    admin_token = make_token("delete-admin", admin.email, settings.supabase_jwt_secret)

    response = client.delete(
        f"/api/v1/users/{member.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 204
    assert get_user_by_auth_id(db_session, "delete-member") is None


def test_admin_cannot_delete_self(client, db_session):
    admin = create_user(
        db_session,
        UserCreate(
            auth_id="self-delete-admin",
            email="self-delete-admin@example.com",
        ),
    )
    admin_token = make_token("self-delete-admin", admin.email, settings.supabase_jwt_secret)

    response = client.delete(
        f"/api/v1/users/{admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Administrators cannot delete themselves"


def test_admin_can_list_only_applicant_users(client, db_session):
    admin = create_user(
        db_session,
        UserCreate(
            auth_id="application-list-admin",
            email="application-list-admin@example.com",
        ),
    )
    applicant = create_user(
        db_session,
        UserCreate(
            auth_id="application-list-applicant",
            email="application-list-applicant@example.com",
        ),
    )
    member = create_user(
        db_session,
        UserCreate(
            auth_id="application-list-member",
            email="application-list-member@example.com",
        ),
    )
    update_user(db_session, applicant.id, UserUpdate(role=UserRole.APPLICANT))
    update_user(db_session, member.id, UserUpdate(role=UserRole.MEMBER))
    admin_token = make_token("application-list-admin", admin.email, settings.supabase_jwt_secret)

    response = client.get(
        "/api/v1/users",
        params={"role": UserRole.APPLICANT.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    count_response = client.get(
        "/api/v1/users/count",
        params={"role": UserRole.APPLICANT.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert [user["auth_id"] for user in response.json()] == ["application-list-applicant"]
    assert count_response.status_code == 200
    assert count_response.json() == 1


def test_applicant_cannot_list_members(client, db_session):
    applicant = create_user(
        db_session,
        UserCreate(
            auth_id="member-list-applicant",
            email="member-list-applicant@example.com",
        ),
    )
    update_user(db_session, applicant.id, UserUpdate(role=UserRole.APPLICANT))
    applicant_token = make_token("member-list-applicant", applicant.email, settings.supabase_jwt_secret)

    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    count_response = client.get(
        "/api/v1/users/count",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )

    assert response.status_code == 403
    assert count_response.status_code == 403
