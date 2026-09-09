"""CRUD operations for Event model"""

from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.db.event.models import Event, event_members
from app.db.event.schemas import EventCreate, EventUpdate
from app.db.user.crud import get_user_by_id
from uuid import UUID


def create_event(db: Session, event: EventCreate, coordinator_id: UUID) -> Event:
    """Create a new event"""
    db_event = Event(
        name=event.name,
        description=event.description,
        start_datetime=event.start_datetime,
        end_datetime=event.end_datetime,
        all_day=event.all_day,
        certification_id=event.certification_id,
        coordinator_id=event.coordinator_id or coordinator_id,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def get_event_by_id(db: Session, event_id: UUID) -> Event | None:
    """Get event by ID"""
    return db.query(Event).filter(Event.id == event_id).first()


def get_all_events(db: Session, skip: int = 0, limit: int = 100) -> list[Event]:
    """Get all events with pagination"""
    return db.query(Event).offset(skip).limit(limit).all()


def _event_filter_query(db: Session, search: str | None = None, certification_id: UUID | None = None, include_all: bool = False):
    query = db.query(Event)
    if not include_all:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today = now.date().isoformat()
        query = query.filter(or_(
            Event.all_day.is_(True) & (func.date(Event.end_datetime) >= today),
            Event.all_day.is_(False) & (Event.end_datetime >= now),
        ))
    if search:
        query = query.filter(Event.name.ilike(f"%{search.strip()}%"))
    if certification_id is not None:
        query = query.filter(Event.certification_id == certification_id)
    return query


def get_upcoming_events(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    certification_id: UUID | None = None,
    include_all: bool = False,
) -> list[Event]:
    """Get filtered events ordered by start date."""
    return (
        _event_filter_query(db, search=search, certification_id=certification_id, include_all=include_all)
        .order_by(Event.start_datetime.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_upcoming_event_count(
    db: Session,
    search: str | None = None,
    certification_id: UUID | None = None,
    include_all: bool = False,
) -> int:
    """Count filtered events."""
    return _event_filter_query(
        db,
        search=search,
        certification_id=certification_id,
        include_all=include_all,
    ).count()


def get_events_by_coordinator(db: Session, coordinator_id: UUID) -> list[Event]:
    """Get all events organized by a specific user"""
    return db.query(Event).filter(Event.coordinator_id == coordinator_id).all()


def update_event(db: Session, event_id: UUID, event_update: EventUpdate) -> Event | None:
    """Update an event"""
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return None
    
    if event_update.name:
        db_event.name = event_update.name
    if event_update.description is not None:
        db_event.description = event_update.description
    if event_update.start_datetime:
        db_event.start_datetime = event_update.start_datetime
    if event_update.end_datetime:
        db_event.end_datetime = event_update.end_datetime
    if event_update.all_day is not None:
        db_event.all_day = event_update.all_day
    if event_update.certification_id is not None:
        db_event.certification_id = event_update.certification_id
    if event_update.coordinator_id is not None:
        db_event.coordinator_id = event_update.coordinator_id
    
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: UUID) -> bool:
    """Delete an event"""
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return False
    
    db.delete(db_event)
    db.commit()
    return True


def add_member_to_event(db: Session, event_id: UUID, user_id: UUID) -> bool:
    """Add a user to an event as a member"""
    db_event = get_event_by_id(db, event_id)
    db_user = get_user_by_id(db, user_id)
    
    if not db_event or not db_user:
        return False
    
    if db_user not in db_event.members:
        db_event.members.append(db_user)
        db.commit()
    
    return True


def remove_member_from_event(db: Session, event_id: UUID, user_id: UUID) -> bool:
    """Remove a user from an event"""
    db_event = get_event_by_id(db, event_id)
    db_user = get_user_by_id(db, user_id)
    
    if not db_event or not db_user:
        return False
    
    if db_user in db_event.members:
        db_event.members.remove(db_user)
        db.commit()
    
    return True


def get_event_members(db: Session, event_id: UUID):
    """Get all members of an event"""
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return []
    return db_event.members
