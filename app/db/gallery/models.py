"""Gallery and picture models."""

from sqlalchemy import Column, String, Text, DateTime, func, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Gallery(Base):
    """A named collection of pictures."""

    __tablename__ = "galleries"

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
    # Set for a gallery that belongs to a news article. Such galleries are managed through the article
    # and kept out of the main gallery listings.
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    __table_args__ = (
        Index("idx_gallery_name", "name"),
    )

    article = relationship("Article", back_populates="gallery")

    pictures = relationship(
        "Picture",
        back_populates="gallery",
        cascade="all, delete-orphan",
    )

    @property
    def picture_count(self) -> int:
        return len(self.pictures)


class Picture(Base):
    """A photo stored within a gallery."""

    __tablename__ = "pictures"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    caption = Column(Text, nullable=True)
    url = Column(String(2048), nullable=True)
    cloudinary_public_id = Column(String(2048), nullable=True)
    gallery_id = Column(
        UUID(as_uuid=True),
        ForeignKey("galleries.id"),
        nullable=False,
        index=True,
    )
    uploaded_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    uploaded_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
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

    gallery = relationship("Gallery", back_populates="pictures")
    uploaded_by = relationship("User", back_populates="pictures")
