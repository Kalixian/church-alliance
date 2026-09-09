from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings
from app.db.certification import Certification, create_certification
from app.db.user import UserCreate, UserRole, UserUpdate, create_user, update_user


def make_token(sub: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "email": email, "iat": now, "exp": now + timedelta(hours=1)},
        settings.supabase_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def test_coordinator_can_manage_certifications(client, db_session):
    coordinator = create_user(
        db_session,
        UserCreate(auth_id="cert-coordinator", email="cert-coordinator@example.com", role=UserRole.COORDINATOR),
    )
    token = make_token(coordinator.auth_id, coordinator.email)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "First Aid", "description": "Emergency response training."},
    )
    assert create_response.status_code == 200
    certification_id = create_response.json()["id"]

    list_response = client.get("/api/v1/certifications?skip=0&limit=10", headers=headers)
    count_response = client.get("/api/v1/certifications/count", headers=headers)
    assert list_response.status_code == 200
    assert count_response.json() == 1

    update_response = client.patch(
        f"/api/v1/certifications/{certification_id}",
        headers=headers,
        json={"name": "Advanced First Aid", "description": "Updated training."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Advanced First Aid"

    delete_response = client.delete(f"/api/v1/certifications/{certification_id}", headers=headers)
    assert delete_response.status_code == 204
    assert db_session.query(Certification).count() == 0


def test_member_cannot_manage_certifications(client, db_session):
    member = create_user(
        db_session,
        UserCreate(auth_id="cert-member", email="cert-member@example.com", role=UserRole.MEMBER),
    )
    update_user(db_session, member.id, UserUpdate(role=UserRole.MEMBER))
    certification = create_certification(db_session, "Member Test")
    headers = {"Authorization": f"Bearer {make_token(member.auth_id, member.email)}"}

    list_response = client.get("/api/v1/certifications")
    create_response = client.post(
        "/api/v1/certifications",
        headers=headers,
        json={"name": "Unauthorized"},
    )
    delete_response = client.delete(
        f"/api/v1/certifications/{certification.id}",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403
    assert delete_response.status_code == 403