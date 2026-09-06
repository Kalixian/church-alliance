"""CRUD operations for Event model"""

from sqlalchemy.orm import Session
from app.db.event.models import Event
from app.db.event.schemas import EventCreate, EventUpdate
from app.db.user.crud import get_user_by_id
from uuid import UUID


def create_event(db: Session, event: EventCreate, organizer_id: UUID) -> Event:
    """Create a new event"""
    db_event = Event(
        name=event.name,
        description=event.description,
        start_datetime=event.start_datetime,
        end_datetime=event.end_datetime,
        organizer_id=organizer_id,
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


def get_events_by_organizer(db: Session, organizer_id: UUID) -> list[Event]:
    """Get all events organized by a specific user"""
    return db.query(Event).filter(Event.organizer_id == organizer_id).all()


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
