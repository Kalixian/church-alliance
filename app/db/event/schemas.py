"""Pydantic schemas for Event model"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.db.user.schemas import UserResponse


class EventBase(BaseModel):
    """Base event schema with common fields"""
    name: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime


class EventCreate(EventBase):
    """Schema for creating an event"""
    pass


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    name: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


class EventResponse(EventBase):
    """Schema for event response"""
    id: UUID
    organizer_id: UUID
    organizer: Optional["UserResponse"] = None
    members: list["UserResponse"] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references after both schemas are defined
EventResponse.model_rebuild()
