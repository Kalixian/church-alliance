"""Pydantic schemas for User model"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.db.user.models import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    role: UserRole = UserRole.APPLICANT


class UserCreate(UserBase):
    """Schema for creating a user"""
    auth_id: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    auth_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Full user schema from database"""
    pass


def mask_last_name(user: UserResponse) -> UserResponse:
    """Return a user response with only the last-name initial exposed."""
    if user.last_name:
        user.last_name = f"{user.last_name[0]}."
    return user
