"""Event domain - models, schemas, and CRUD operations"""

from .models import Event, event_members
from .schemas import EventBase, EventCreate, EventUpdate, EventResponse
from .crud import (
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

__all__ = [
    # Models
    "Event",
    "event_members",
    # Schemas
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    # CRUD
    "create_event",
    "get_event_by_id",
    "get_all_events",
    "get_upcoming_events",
    "get_upcoming_event_count",
    "get_events_by_coordinator",
    "update_event",
    "delete_event",
    "add_member_to_event",
    "remove_member_from_event",
    "get_event_members",
]
