"""Pydantic schemas for galleries and pictures."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GalleryBase(BaseModel):
    name: str


class GalleryCreate(GalleryBase):
    pass


class GalleryUpdate(BaseModel):
    name: Optional[str] = None


class GalleryResponse(GalleryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    picture_count: int

    model_config = ConfigDict(from_attributes=True)


class PictureBase(BaseModel):
    caption: Optional[str] = None
    url: Optional[str] = None
    cloudinary_public_id: Optional[str] = None
    gallery_id: Optional[UUID] = None


class PictureCreate(PictureBase):
    pass


class PictureUpdate(BaseModel):
    caption: Optional[str] = None
    gallery_id: Optional[UUID] = None


class PictureUploadConfirm(BaseModel):
    """Fields from Cloudinary's signed upload response, plus the picture's details."""
    public_id: str = Field(min_length=1, max_length=2048)
    version: int
    signature: str = Field(min_length=1, max_length=128)
    caption: Optional[str] = None
    gallery_id: Optional[UUID] = None


class UploadSignatureResponse(BaseModel):
    upload_url: str
    fields: dict[str, str]


class PictureResponse(PictureBase):
    id: UUID
    uploaded_by_id: UUID
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
