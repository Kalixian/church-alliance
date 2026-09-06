from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.user import UserResponse
from app.db.event import (
    Event,
    EventResponse,
    EventCreate,
    EventUpdate,
    create_event,
    get_event_by_id,
    get_all_events,
    get_events_by_organizer,
    update_event,
    delete_event,
    add_member_to_event,
    remove_member_from_event,
    get_event_members,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse)
def create_event_route(
    event: EventCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Create a new event (current user is the organizer)"""
    db_event = create_event(db, event, current_user.id)
    return db_event


@router.get("", response_model=list[EventResponse])
def list_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all events"""
    events = get_all_events(db, skip=skip, limit=limit)
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
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
    
    return db_event


@router.patch("/{event_id}", response_model=EventResponse)
def update_event_route(
    event_id: str,
    event_update: EventUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Update an event (only the organizer can update)"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if db_event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer can update this event",
        )
    
    updated_event = update_event(db, event_uuid, event_update)
    return updated_event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_route(
    event_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Delete an event (only the organizer can delete)"""
    try:
        from uuid import UUID
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    db_event = get_event_by_id(db, event_uuid)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if db_event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer can delete this event",
        )
    
    delete_event(db, event_uuid)
    return None


@router.post("/{event_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_event_member(
    event_id: str,
    user_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
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
    
    # Allow organizer or the user themselves to add members
    if db_event.organizer_id != current_user.id and member_uuid != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add members to this event",
        )
    
    success = add_member_to_event(db, event_uuid, member_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Event or user not found")
    
    return None


@router.delete("/{event_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_member(
    event_id: str,
    user_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
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
    
    # Allow organizer or the user themselves to remove members
    if db_event.organizer_id != current_user.id and member_uuid != current_user.id:
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
    return members


@router.get("/organizer/{user_id}", response_model=list[EventResponse])
def get_organizer_events(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get all events organized by a specific user"""
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    events = get_events_by_organizer(db, user_uuid)
    return events
