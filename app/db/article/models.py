"""Article database model."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Article(Base):
    """A rich-text article created by a user."""

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(JSON, nullable=False)
    summary = Column(Text, nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_article_creator_id", "creator_id"),
        Index("idx_article_created_at", "created_at"),
    )

    creator = relationship("User", back_populates="articles")
    gallery = relationship(
        "Gallery",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def gallery_id(self):
        return self.gallery.id if self.gallery else None

    @property
    def cover_url(self) -> str | None:
        """URL of the article's first photo, used as its thumbnail in listings."""
        if not self.gallery:
            return None
        return next((picture.url for picture in self.gallery.pictures if picture.url), None)
