from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.auth.dependencies import allow_roles, disallowed_roles, get_current_user
from app.db.database import get_db
from sqlalchemy.orm import Session

from app.db.user import (
    UserBase,
    UserResponse,
    UserCreate,
    UserUpdate,
    create_user,
    get_user_by_id,
    get_user_by_auth_id,
    get_all_users,
    get_users_sorted,
    get_user_count,
    get_users_by_role,
    update_user,
    delete_user,
)
from app.db.user.models import UserRole
from app.db.user.schemas import mask_last_name
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])

# @router.post("", response_model=UserResponse)
# def create_user_route(
#     user: UserBase,
#     admin: Annotated[UserResponse, Depends(allow_roles(UserRole.ADMIN))],
#     db: Session = Depends(get_db)
# ):
#     """Create a new user."""
#     db_user = create_user(db, user)
#     return db_user

@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: UUID,
    new_role: UserRole,
    admin: Annotated[
        UserResponse,
        Depends(allow_roles(UserRole.ADMINISTRATOR)),
    ],
    db: Session = Depends(get_db),
):
    """Update a user's role (administrator only)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Administrators cannot change their own role")
    updated_user = update_user(db, user_id, UserUpdate(role=new_role))
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_route(
    user_id: UUID,
    admin: Annotated[
        UserResponse,
        Depends(allow_roles(UserRole.ADMINISTRATOR)),
    ],
    db: Session = Depends(get_db),
):
    """Delete a user (administrator only)."""
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Administrators cannot delete themselves")
    if not delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/roles", response_model=list[UserRole])
def list_user_roles(
    admin: Annotated[UserResponse, Depends(allow_roles(UserRole.ADMINISTRATOR))],
):
    """ Get all roles available to users - only for admins."""
    return list(UserRole)


@router.get("/count", response_model=int)
def count_users(
    user: Annotated[UserResponse, Depends(disallowed_roles(UserRole.APPLICANT))],
    role: UserRole | None = None,
    exclude_role: UserRole | None = None,
    db: Session = Depends(get_db),
):
    """ Get the total number of users."""
    return get_user_count(db, role=role, exclude_role=exclude_role)


@router.get("", response_model=list[UserResponse])
def list_users(
    user: Annotated[UserResponse, Depends(disallowed_roles(UserRole.APPLICANT))],
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "last_name",
    descending: bool = False,
    role: UserRole | None = None,
    exclude_role: UserRole | None = None,
    db: Session = Depends(get_db),
):
    """List users with pagination and sorting. Only for non-applicants."""
    allowed_sort_fields = {"first_name", "last_name", "email", "role"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    return get_users_sorted(
        db,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        descending=descending,
        role=role,
        exclude_role=exclude_role,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """ Get a user by ID. Users can only access their own data unless they are member of the site."""
    if current_user.role == UserRole.APPLICANT and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    response = UserResponse.model_validate(user)
    return mask_last_name(response) if current_user.role == UserRole.APPLICANT else response