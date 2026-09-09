from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.v1.auth.dependencies import get_current_user, allow_roles
from app.db.database import get_db
from app.db.user import UserResponse, UserRole
from app.db.certification import (
    CertificationResponse,
    CertificationCreate,
    CertificationUpdate,
    create_certification,
    get_certification_by_id,
    get_all_certifications,
    get_certification_count,
    update_certification,
    delete_certification,
    get_users_by_certification,
)

router = APIRouter(prefix="/certifications", tags=["certifications"])

certification_managers = allow_roles(UserRole.ADMINISTRATOR, UserRole.COORDINATOR)


@router.post("", response_model=CertificationResponse)
def create_certification_route(
    certification: CertificationCreate,
    current_user: Annotated[UserResponse, Depends(certification_managers)],
    db: Session = Depends(get_db),
):
    """Create a new certification (admin-only)"""
    db_cert = create_certification(db, certification.name, certification.description)
    return db_cert


@router.get("", response_model=list[CertificationResponse])
def list_certifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_all_certifications(db, skip=skip, limit=limit)


@router.get("/count", response_model=int)
def count_certifications(
    db: Session = Depends(get_db),
):
    return get_certification_count(db)


@router.get("/{cert_id}", response_model=CertificationResponse)
def get_cert(cert_id: str, db: Session = Depends(get_db)):
    try:
        cert_uuid = UUID(cert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid certification ID")
    cert = get_certification_by_id(db, cert_uuid)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    return cert


@router.patch("/{cert_id}", response_model=CertificationResponse)
def update_cert(
    cert_id: str,
    cert_update: CertificationUpdate,
    current_user: Annotated[UserResponse, Depends(certification_managers)],
    db: Session = Depends(get_db),
):
    try:
        cert_uuid = UUID(cert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid certification ID")
    cert = update_certification(db, cert_uuid, name=cert_update.name, description=cert_update.description)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    return cert


@router.delete("/{cert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cert_route(
    cert_id: str,
    current_user: Annotated[UserResponse, Depends(certification_managers)],
    db: Session = Depends(get_db),
):
    try:
        cert_uuid = UUID(cert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid certification ID")
    success = delete_certification(db, cert_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Certification not found")
    return None


@router.get("/{cert_id}/users", response_model=list[UserResponse])
def get_cert_users(cert_id: str, db: Session = Depends(get_db)):
    try:
        cert_uuid = UUID(cert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid certification ID")
    users = get_users_by_certification(db, certification_id=cert_uuid)
    return users
