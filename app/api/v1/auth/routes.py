from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import get_current_user, allow_roles
from app.db.user import UserRole, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sync-user", response_model=UserResponse)
def sync_user(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    return current_user


@router.get("/admin-only", response_model=UserResponse)
def admin_only(
    current_user: Annotated[
        UserResponse,
        Depends(allow_roles(UserRole.ADMINISTRATOR)),
    ],
):
    return current_user

