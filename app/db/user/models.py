"""User model and role enum"""

from sqlalchemy import Column, String, DateTime, func, Index, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    """Allowed user roles"""
    APPLICANT = "applicant"
    MEMBER = "member"
    COORDINATOR = "coordinator"
    ADMINISTRATOR = "administrator"


class User(Base):
    """User model for authentication and permissions"""
    
    __tablename__ = "users"
    
    # Unique internal ID (primary key)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # External authentication ID (e.g., Supabase UID)
    auth_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Email address
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Profile name fields
    first_name = Column(
        String(255),
        nullable=True,
    )

    last_name = Column(
        String(255),
        nullable=True,
    )
    
    # Role for permissions (restricted to applicant, member, administrator)
    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.APPLICANT,
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
        Index("idx_auth_id", "auth_id"),
        Index("idx_email", "email"),
        Index("idx_role", "role"),
    )
    
    # Relationships
    organized_events = relationship(
        "Event",
        back_populates="coordinator",
        foreign_keys="Event.coordinator_id",
        cascade="all, delete-orphan",
    )
    event_memberships = relationship(
        "Event",
        secondary="event_members",
        back_populates="members",
    )
    certifications = relationship(
        "Certification",
        secondary="user_certifications",
        back_populates="users",
    )
    assets = relationship(
        "Asset",
        secondary="user_assets",
        back_populates="users",
    )
    pictures = relationship(
        "Picture",
        back_populates="uploaded_by",
    )
    articles = relationship(
        "Article",
        back_populates="creator",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
