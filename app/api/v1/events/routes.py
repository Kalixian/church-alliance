from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import (
    MANAGER_ROLES,
    ensure_owner_or_role,
    get_current_user,
    get_optional_current_user,
    require_confirmed,
    require_manager,
)
from app.db.database import get_db
from app.db.user import UserResponse, UserRole, get_user_by_id
from app.db.event import (
    Event,
    EventResponse,
    EventCreate,
    EventUpdate,
    create_event,
    get_event_by_id,
    get_all_events,
    get_upcoming_events,
    get_upcoming_event_count,
    get_events_by_coordinator,
    update_event,
    delete_event,
    add_member_to_event,
    remove_member_from_event,
    get_event_members,
)

router = APIRouter(prefix="/events", tags=["events"])

ADMIN_ONLY = frozenset({UserRole.ADMINISTRATOR})


def _mask_user_names(user: UserResponse | None):
    if user and user.last_name:
        user.last_name = f"{user.last_name[0]}."


def _event_response(event: Event, viewer: UserResponse | None) -> EventResponse:
    response = EventResponse.model_validate(event)
    response.certification_name = event.certification.name if event.certification else None
    if viewer is None or viewer.role == UserRole.APPLICANT:
        _mask_user_names(response.coordinator)
        for member in response.members:
            _mask_user_names(member)
    return response


def _parse_certification_id(certification_id: str | None):
    if not certification_id:
        return None
    try:
        from uuid import UUID
        return UUID(certification_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid certification ID") from exc


@router.post("", response_model=EventResponse)
def create_event_route(
    event: EventCreate,
    current_user: Annotated[
        UserResponse,
        Depends(require_manager()),
    ],
    db: Session = Depends(get_db),
):
    """Create an event for the current or selected qualified coordinator."""
    coordinator_id = event.coordinator_id or current_user.id
    coordinator = get_user_by_id(db, coordinator_id)
    if not coordinator or coordinator.role not in MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Events can only be assigned to coordinators or administrators",
        )
    db_event = create_event(db, event, current_user.id)
    return _event_response(db_event, current_user)


@router.get("", response_model=list[EventResponse])
def list_events(
    viewer: Annotated[UserResponse | None, Depends(get_optional_current_user)],
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all events"""
    events = get_all_events(db, skip=skip, limit=limit)
    return [_event_response(event, viewer) for event in events]


@router.get("/upcoming", response_model=list[EventResponse])
def list_upcoming_events(
    viewer: Annotated[UserResponse | None, Depends(get_optional_current_user)],
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    include_all: bool = False,
    certification_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Get filtered events ordered by start date."""
    parsed_certification_id = _parse_certification_id(certification_id)
    events = get_upcoming_events(
        db,
        skip=skip,
        limit=limit,
        search=search,
        certification_id=parsed_certification_id,
        include_all=include_all,
    )
    return [_event_response(event, viewer) for event in events]


@router.get("/upcoming/count", response_model=int)
def count_upcoming_events(
    search: str | None = None,
    include_all: bool = False,
    certification_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Get the count of filtered events."""
    parsed_certification_id = _parse_certification_id(certification_id)
    return get_upcoming_event_count(
        db,
        search=search,
        certification_id=parsed_certification_id,
        include_all=include_all,
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    viewer: Annotated[UserResponse | None, Depends(get_optional_current_user)],
    db: Session = Depends(get_db),
):
    """Get a specific event by ID"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return _event_response(db_event, viewer)


@router.patch("/{event_id}", response_model=EventResponse)
def update_event_route(
    event_id: str,
    event_update: EventUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Update an event (only the coordinator can update)"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    ensure_owner_or_role(
        current_user,
        db_event.coordinator_id,
        "Only an administrator or the event coordinator can update this event",
        roles=ADMIN_ONLY,
    )

    if event_update.coordinator_id is not None:
        coordinator = get_user_by_id(db, event_update.coordinator_id)
        if not coordinator or coordinator.role not in MANAGER_ROLES:
            raise HTTPException(status_code=400, detail="Events can only be assigned to coordinators or administrators")
    
    updated_event = update_event(db, event_uuid, event_update)
    return _event_response(updated_event, current_user)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_route(
    event_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Delete an event (only the coordinator can delete)"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    ensure_owner_or_role(
        current_user,
        db_event.coordinator_id,
        "Only an administrator or the event coordinator can delete this event",
        roles=ADMIN_ONLY,
    )
    
    delete_event(db, event_uuid)
    return None


@router.post("/{event_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_event_member(
    event_id: str,
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_confirmed("Applicants cannot register for events"))],
    db: Session = Depends(get_db),
):
    """Add a user as a member to an event"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
        member_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID or user ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Allow coordinator/admin or the user themselves to add members
    if db_event.coordinator_id != current_user.id and member_uuid != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add members to this event",
        )
    
    success = add_member_to_event(db, event_uuid, member_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Event or user not found")
    
    return None


@router.post("/{event_id}/register", status_code=status.HTTP_204_NO_CONTENT)
def register_for_event(
    event_id: str,
    current_user: Annotated[UserResponse, Depends(require_confirmed("Applicants cannot register for events"))],
    db: Session = Depends(get_db),
):
    """Register the current non-applicant user for an event."""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid event ID") from exc
    if not get_event_by_id(db, event_uuid):
        raise HTTPException(status_code=404, detail="Event not found")
    if not add_member_to_event(db, event_uuid, current_user.id):
        raise HTTPException(status_code=404, detail="Event or user not found")


@router.delete("/{event_id}/register", status_code=status.HTTP_204_NO_CONTENT)
def deregister_from_event(
    event_id: str,
    current_user: Annotated[UserResponse, Depends(require_confirmed("Applicants cannot deregister from events"))],
    db: Session = Depends(get_db),
):
    """Deregister the current non-applicant user from an event."""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid event ID") from exc
    if not get_event_by_id(db, event_uuid):
        raise HTTPException(status_code=404, detail="Event not found")
    if not remove_member_from_event(db, event_uuid, current_user.id):
        raise HTTPException(status_code=404, detail="Registration not found")


@router.delete("/{event_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_member(
    event_id: str,
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_confirmed("Applicants cannot deregister from events"))],
    db: Session = Depends(get_db),
):
    """Remove a user from an event"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
        member_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID or user ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Allow coordinator/admin or the user themselves to remove members
    if db_event.coordinator_id != current_user.id and member_uuid != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove members from this event",
        )
    
    success = remove_member_from_event(db, event_uuid, member_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Event or user not found")
    
    return None


@router.get("/{event_id}/members", response_model=list[UserResponse])
def get_event_members_route(
    event_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Get all members of an event"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    members = get_event_members(db, event_uuid)
    responses = [UserResponse.model_validate(member) for member in members]
    if current_user.role == UserRole.APPLICANT:
        for member in responses:
            _mask_user_names(member)
    return responses


@router.get("/coordinator/{user_id}", response_model=list[EventResponse])
def get_coordinator_events(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get all events organized by a specific user"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    events = get_events_by_coordinator(db, user_uuid)
    return events
