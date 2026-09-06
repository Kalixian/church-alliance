"""Asset domain models for user equipment and supplies."""

from sqlalchemy import Column, String, Text, DateTime, func, Index, ForeignKey, Table, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


user_assets = Table(
    "user_assets",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("asset_id", UUID(as_uuid=True), ForeignKey("assets.id"), primary_key=True),
    Column("quantity", String(64), nullable=True),
    Column("notes", String(512), nullable=True),
    Column("available", Boolean, default=True, nullable=False),
)


class Asset(Base):
    """Asset definition for equipment or supplies a user can bring."""

    __tablename__ = "assets"

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
        Index("idx_asset_name", "name"),
    )

    users = relationship(
        "User",
        secondary=user_assets,
        back_populates="assets",
    )
