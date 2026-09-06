"""Certification domain models for user qualifications."""

from sqlalchemy import Column, String, Text, DateTime, func, Index, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


user_certifications = Table(
    "user_certifications",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("certification_id", UUID(as_uuid=True), ForeignKey("certifications.id"), primary_key=True),
    Column("issued_at", DateTime, nullable=True),
    Column("expires_at", DateTime, nullable=True),
    Column("notes", String(512), nullable=True),
)


class Certification(Base):
    """Certification definition used to qualify a user for work."""

    __tablename__ = "certifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    description = Column(
        Text,
        nullable=True,
    )
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

    __table_args__ = (
        Index("idx_certification_name", "name"),
    )

    users = relationship(
        "User",
        secondary=user_certifications,
        back_populates="certifications",
    )
