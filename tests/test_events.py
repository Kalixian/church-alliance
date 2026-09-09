from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings
from app.db.certification import create_certification
from app.db.user import UserCreate, UserRole, create_user


def make_token(sub: str, email: str) -> str:
    return jwt.encode(
        {"sub": sub, "email": email},
        settings.supabase_jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def test_create_date_only_event(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="date-event-user", email="date-event@example.com", role=UserRole.COORDINATOR),
    )

    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(user.auth_id, user.email)}"},
        json={
            "name": "Community Day",
            "start_datetime": "2026-10-10",
            "end_datetime": "2026-10-11",
            "all_day": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["all_day"] is True
    assert data["start_datetime"].startswith("2026-10-10T00:00:00")
    assert data["end_datetime"].startswith("2026-10-11T00:00:00")


def test_create_timed_event(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="timed-event-user", email="timed-event@example.com", role=UserRole.COORDINATOR),
    )

    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(user.auth_id, user.email)}"},
        json={
            "name": "Evening Service",
            "start_datetime": "2026-10-10T18:00:00",
            "end_datetime": "2026-10-10T20:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["all_day"] is False


def test_qualified_user_can_assign_event_to_another_coordinator(client, db_session):
    creator = create_user(
        db_session,
        UserCreate(auth_id="event-creator", email="event-creator@example.com", role=UserRole.ADMINISTRATOR),
    )
    coordinator = create_user(
        db_session,
        UserCreate(auth_id="event-coordinator", email="event-coordinator@example.com", role=UserRole.COORDINATOR),
    )
    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(creator.auth_id, creator.email)}"},
        json={
            "name": "Assigned Training",
            "start_datetime": "2026-10-10T18:00:00",
            "end_datetime": "2026-10-10T20:00:00",
            "coordinator_id": str(coordinator.id),
        },
    )

    assert response.status_code == 200
    assert response.json()["coordinator_id"] == str(coordinator.id)


def test_event_registration_and_deregistration(client, db_session):
    coordinator = create_user(
        db_session,
        UserCreate(auth_id="registration-coordinator", email="registration-coordinator@example.com", role=UserRole.COORDINATOR),
    )
    member = create_user(
        db_session,
        UserCreate(auth_id="registration-member", email="registration-member@example.com", role=UserRole.MEMBER),
    )
    create_response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(coordinator.auth_id, coordinator.email)}"},
        json={
            "name": "Registration Event",
            "start_datetime": "2026-10-10T18:00:00",
            "end_datetime": "2026-10-10T20:00:00",
        },
    )
    event_id = create_response.json()["id"]
    member_token = make_token(member.auth_id, member.email)

    register_response = client.post(
        f"/api/v1/events/{event_id}/register",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    deregister_response = client.delete(
        f"/api/v1/events/{event_id}/register",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert register_response.status_code == 204
    assert deregister_response.status_code == 204


def test_only_admin_or_event_coordinator_can_edit_and_delete(client, db_session):
    coordinator = create_user(
        db_session,
        UserCreate(auth_id="owner-coordinator", email="owner-coordinator@example.com", role=UserRole.COORDINATOR),
    )
    other_coordinator = create_user(
        db_session,
        UserCreate(auth_id="other-coordinator", email="other-coordinator@example.com", role=UserRole.COORDINATOR),
    )
    administrator = create_user(
        db_session,
        UserCreate(auth_id="event-administrator", email="event-administrator@example.com", role=UserRole.ADMINISTRATOR),
    )
    event_response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(coordinator.auth_id, coordinator.email)}"},
        json={
            "name": "Owned Event",
            "start_datetime": "2026-10-10T18:00:00",
            "end_datetime": "2026-10-10T20:00:00",
        },
    )
    event_id = event_response.json()["id"]

    denied_update = client.patch(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {make_token(other_coordinator.auth_id, other_coordinator.email)}"},
        json={"name": "Denied"},
    )
    owner_update = client.patch(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {make_token(coordinator.auth_id, coordinator.email)}"},
        json={"name": "Updated by Owner"},
    )
    admin_delete = client.delete(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {make_token(administrator.auth_id, administrator.email)}"},
    )

    assert denied_update.status_code == 403
    assert owner_update.status_code == 200
    assert admin_delete.status_code == 204


def test_public_event_names_use_last_initial(client, db_session):
    coordinator = create_user(
        db_session,
        UserCreate(
            auth_id="public-name-coordinator",
            email="public-name@example.com",
            first_name="Jordan",
            last_name="Morrison",
            role=UserRole.COORDINATOR,
        ),
    )
    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(coordinator.auth_id, coordinator.email)}"},
        json={
            "name": "Public Name Event",
            "start_datetime": "2026-10-10T18:00:00",
            "end_datetime": "2026-10-10T20:00:00",
        },
    )
    event_id = response.json()["id"]

    public_response = client.get(f"/api/v1/events/{event_id}")
    authenticated_response = client.get(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": f"Bearer {make_token(coordinator.auth_id, coordinator.email)}"},
    )

    assert public_response.json()["coordinator"]["last_name"] == "M."
    assert authenticated_response.json()["coordinator"]["last_name"] == "Morrison"


def test_create_single_day_event(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="single-day-event-user", email="single-day-event@example.com", role=UserRole.COORDINATOR),
    )

    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(user.auth_id, user.email)}"},
        json={
            "name": "One Day Event",
            "start_datetime": "2026-10-10",
            "end_datetime": "2026-10-10",
            "all_day": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["all_day"] is True


def test_date_only_event_requires_all_day_flag(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="invalid-date-event-user", email="invalid-date-event@example.com", role=UserRole.COORDINATOR),
    )

    response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {make_token(user.auth_id, user.email)}"},
        json={
            "name": "Missing Schedule Mode",
            "start_datetime": "2026-10-10",
            "end_datetime": "2026-10-11",
        },
    )

    assert response.status_code == 422


def test_upcoming_events_are_active_ordered_and_paginated(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="upcoming-event-user", email="upcoming-event@example.com", role=UserRole.COORDINATOR),
    )
    token = make_token(user.auth_id, user.email)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for name, start_offset, end_offset in (
        ("Later", timedelta(days=2), timedelta(days=3)),
        ("Ongoing", -timedelta(hours=1), timedelta(hours=1)),
        ("Expired", -timedelta(days=3), -timedelta(days=1)),
    ):
        response = client.post(
            "/api/v1/events",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": name,
                "start_datetime": (now + start_offset).isoformat(),
                "end_datetime": (now + end_offset).isoformat(),
            },
        )
        assert response.status_code == 200

    response = client.get("/api/v1/events/upcoming?skip=0&limit=1")
    count_response = client.get("/api/v1/events/upcoming/count")

    assert response.status_code == 200
    assert [event["name"] for event in response.json()] == ["Ongoing"]
    assert count_response.status_code == 200
    assert count_response.json() == 2


def test_event_filters_support_title_date_and_certification(client, db_session):
    user = create_user(
        db_session,
        UserCreate(auth_id="filtered-event-user", email="filtered-event@example.com", role=UserRole.COORDINATOR),
    )
    token = make_token(user.auth_id, user.email)
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    event_response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "name": "Certified Rescue Training",
            "start_datetime": (now + timedelta(days=1)).isoformat(),
            "end_datetime": (now + timedelta(days=1, hours=2)).isoformat(),
        },
    )
    assert event_response.status_code == 200
    event_id = event_response.json()["id"]
    certification = create_certification(db_session, "Rescue Certified")
    update_response = client.patch(
        f"/api/v1/events/{event_id}",
        headers=headers,
        json={"certification_id": str(certification.id)},
    )
    assert update_response.status_code == 200

    search_response = client.get("/api/v1/events/upcoming?search=Rescue")
    all_events_response = client.get("/api/v1/events/upcoming?include_all=true&search=Certified")
    certification_response = client.get(
        f"/api/v1/events/upcoming?certification_id={certification.id}",
    )

    assert [event["name"] for event in search_response.json()] == ["Certified Rescue Training"]
    assert [event["name"] for event in all_events_response.json()] == ["Certified Rescue Training"]
    assert [event["name"] for event in certification_response.json()] == ["Certified Rescue Training"]
    assert certification_response.json()[0]["certification_name"] == "Rescue Certified"