from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.v1.auth.dependencies import sync_current_user, allow_roles
from app.db.user import UserRole, UserResponse
from app.db.user.schemas import mask_last_name

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sync-user", response_model=UserResponse)
def sync_user(current_user: Annotated[UserResponse, Depends(sync_current_user)]):
    return mask_last_name(current_user) if current_user.role == UserRole.APPLICANT else current_user


@router.get("/admin-only", response_model=UserResponse)
def admin_only(
    current_user: Annotated[
        UserResponse,
        Depends(allow_roles(UserRole.ADMINISTRATOR)),
    ],
):
    return current_user

