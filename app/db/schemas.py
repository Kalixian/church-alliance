"""Pydantic schemas - re-exports from domain modules for backwards compatibility"""

from app.db.user import UserBase, UserCreate, UserUpdate, UserResponse, UserInDB
from app.db.event import EventBase, EventCreate, EventUpdate, EventResponse

# Update forward references for EventResponse to resolve UserResponse
EventResponse.model_rebuild()

__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
]


