from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.v1.auth.dependencies import get_current_user, allow_roles
from app.db.database import get_db
from app.db.user import UserResponse, UserRole
from app.db.asset import (
    AssetResponse,
    AssetCreate,
    AssetUpdate,
    create_asset,
    get_asset_by_id,
    get_all_assets,
    update_asset,
    delete_asset,
    get_users_by_asset,
)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("", response_model=AssetResponse)
def create_asset_route(
    asset: AssetCreate,
    current_user: Annotated[UserResponse, Depends(allow_roles(UserRole.ADMINISTRATOR))],
    db: Session = Depends(get_db),
):
    db_asset = create_asset(db, asset.name, asset.description)
    return db_asset


@router.get("", response_model=list[AssetResponse])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_assets(db, skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")
    asset = get_asset_by_id(db, asset_uuid)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset_route(
    asset_id: str,
    asset_update: AssetUpdate,
    current_user: Annotated[UserResponse, Depends(allow_roles(UserRole.ADMINISTRATOR))],
    db: Session = Depends(get_db),
):
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")
    asset = update_asset(db, asset_uuid, name=asset_update.name, description=asset_update.description)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_route(
    asset_id: str,
    current_user: Annotated[UserResponse, Depends(allow_roles(UserRole.ADMINISTRATOR))],
    db: Session = Depends(get_db),
):
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")
    success = delete_asset(db, asset_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None


@router.get("/{asset_id}/users", response_model=list[UserResponse])
def get_asset_users(asset_id: str, db: Session = Depends(get_db)):
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")
    users = get_users_by_asset(db, asset_id=asset_uuid)
    return users
