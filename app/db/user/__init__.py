"""User domain - models, schemas, and CRUD operations"""

from .models import User, UserRole
from .schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserInDB
from .crud import (
    create_user,
    get_user_by_id,
    get_user_by_auth_id,
    get_user_by_email,
    get_all_users,
    get_users_sorted,
    get_user_count,
    get_users_by_role,
    update_user,
    update_user_email,
    update_user_names,
    delete_user,
)

__all__ = [
    # Models
    "User",
    "UserRole",
    # Schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # CRUD
    "create_user",
    "get_user_by_id",
    "get_user_by_auth_id",
    "get_user_by_email",
    "get_all_users",
    "get_users_sorted",
    "get_user_count",
    "get_users_by_role",
    "update_user",
    "update_user_email",
    "update_user_names",
    "delete_user",
]
