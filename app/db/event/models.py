"""Event model and event members association table"""

from sqlalchemy import Column, String, DateTime, func, Index, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


# Association table for Event members (many-to-many relationship)
event_members = Table(
    "event_members",
    Base.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
)


class Event(Base):
    """Event model for church events"""
    
    __tablename__ = "events"
    
    # Unique internal ID (primary key)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Event name
    name = Column(
        String(255),
        nullable=False,
        index=True,
    )
    
    # Event description
    description = Column(
        Text,
        nullable=True,
    )
    
    # Start date/time
    start_datetime = Column(
        DateTime,
        nullable=False,
        index=True,
    )
    
    # End date/time
    end_datetime = Column(
        DateTime,
        nullable=False,
    )
    
    # Organizer (user that created the event)
    organizer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_organizer_id", "organizer_id"),
        Index("idx_start_datetime", "start_datetime"),
        Index("idx_name", "name"),
    )
    
    # Relationships
    organizer = relationship(
        "User",
        back_populates="organized_events",
        foreign_keys=[organizer_id],
    )
    members = relationship(
        "User",
        secondary=event_members,
        back_populates="event_memberships",
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name={self.name}, organizer_id={self.organizer_id})>"
