"""CRUD operations for certifications."""

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.certification.models import Certification, user_certifications
from app.db.user.models import User
from uuid import UUID
from sqlalchemy import select


def create_certification(db: Session, name: str, description: str | None = None) -> Certification:
    """Create a new certification."""
    certification = Certification(name=name, description=description)
    db.add(certification)
    db.commit()
    db.refresh(certification)
    return certification


def get_certification_by_id(db: Session, certification_id: UUID) -> Certification | None:
    """Get a certification by its ID."""
    return db.query(Certification).filter(Certification.id == certification_id).first()


def get_certification_by_name(db: Session, name: str) -> Certification | None:
    """Get a certification by its name."""
    return db.query(Certification).filter(Certification.name == name).first()


def get_all_certifications(db: Session, skip: int = 0, limit: int = 100) -> list[Certification]:
    """Get all certifications."""
    return db.query(Certification).order_by(Certification.name.asc()).offset(skip).limit(limit).all()


def get_certification_count(db: Session) -> int:
    """Get the total number of certifications."""
    return db.query(Certification).count()


def update_certification(db: Session, certification_id: UUID, name: str | None = None, description: str | None = None) -> Certification | None:
    """Update an existing certification."""
    cert = get_certification_by_id(db, certification_id)
    if not cert:
        return None
    if name is not None:
        cert.name = name
    if description is not None:
        cert.description = description
    db.commit()
    db.refresh(cert)
    return cert


def delete_certification(db: Session, certification_id: UUID) -> bool:
    """Delete a certification."""
    cert = get_certification_by_id(db, certification_id)
    if not cert:
        return False
    db.delete(cert)
    db.commit()
    return True


def assign_certification_to_user(
    db: Session,
    user_id: UUID,
    certification_id: UUID,
    issued_at: datetime | None = None,
    expires_at: datetime | None = None,
    notes: str | None = None,
) -> bool:
    """Assign a certification to a user with optional metadata."""
    user = db.query(User).filter(User.id == user_id).first()
    cert = get_certification_by_id(db, certification_id)
    if not user or not cert:
        return False

    exists = db.execute(
        select(user_certifications).where(
            user_certifications.c.user_id == user_id,
            user_certifications.c.certification_id == certification_id,
        )
    ).first()
    if exists:
        return True

    db.execute(
        user_certifications.insert().values(
            user_id=user_id,
            certification_id=certification_id,
            issued_at=issued_at,
            expires_at=expires_at,
            notes=notes,
        )
    )
    db.commit()
    return True


def remove_certification_from_user(db: Session, user_id: UUID, certification_id: UUID) -> bool:
    """Remove a certification assignment from a user."""
    res = db.execute(
        user_certifications.delete().where(
            user_certifications.c.user_id == user_id,
            user_certifications.c.certification_id == certification_id,
        )
    )
    db.commit()
    return (res.rowcount or 0) > 0


def get_users_by_certification(
    db: Session,
    certification_id: UUID | None = None,
    certification_name: str | None = None,
) -> list[User]:
    """Get all users associated with a specific certification."""
    query = db.query(User).join(user_certifications).join(Certification)
    if certification_id is not None:
        query = query.filter(Certification.id == certification_id)
    if certification_name is not None:
        query = query.filter(Certification.name == certification_name)
    return query.distinct().all()
