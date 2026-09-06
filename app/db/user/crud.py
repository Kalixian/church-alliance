"""CRUD operations for User model"""

from sqlalchemy.orm import Session
from app.db.user.models import User, UserRole
from app.db.user.schemas import UserCreate, UserUpdate
from uuid import UUID


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    is_first_user = db.query(User).first() is None
    db_user = User(
        auth_id=user.auth_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=UserRole.ADMINISTRATOR if is_first_user else user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Get user by internal ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_auth_id(db: Session, auth_id: str) -> User | None:
    """Get user by external auth ID"""
    return db.query(User).filter(User.auth_id == auth_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()


def get_users_sorted(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "last_name",
    descending: bool = False,
    role: UserRole | None = None,
    exclude_role: UserRole | None = None,
) -> list[User]:
    """Get users with pagination and sorting."""
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if exclude_role is not None:
        query = query.filter(User.role != exclude_role)

    sortable_columns = {
        "first_name": User.first_name,
        "last_name": User.last_name,
        "email": User.email,
        "role": User.role,
    }

    sort_field = sortable_columns.get(sort_by, User.last_name)
    if sort_by == "role":
        if descending:
            query = query.order_by(User.role.desc(), User.last_name.desc())
        else:
            query = query.order_by(User.role.asc(), User.last_name.asc())
    else:
        if descending:
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())

    return query.offset(skip).limit(limit).all()


def get_user_count(
    db: Session,
    role: UserRole | None = None,
    exclude_role: UserRole | None = None,
) -> int:
    """Count users with optional role inclusion or exclusion."""
    query = db.query(User)
    if role is not None:
        query = query.filter(User.role == role)
    if exclude_role is not None:
        query = query.filter(User.role != exclude_role)
    return query.count()


def get_users_by_role(db: Session, role: UserRole) -> list[User]:
    """Get all users with a specific role"""
    return db.query(User).filter(User.role == role).all()


def update_user(db: Session, user_id: UUID, user_update: UserUpdate) -> User | None:
    """Update a user"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    if user_update.email:
        db_user.email = user_update.email
    if user_update.first_name is not None:
        db_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        db_user.last_name = user_update.last_name
    if user_update.role:
        db_user.role = user_update.role
    
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_email(db: Session, user_id: UUID, new_email: str) -> User | None:
    """Update a user's email if it differs from the current value."""
    db_user = get_user_by_id(db, user_id)
    if not db_user or db_user.email == new_email:
        return db_user

    db_user.email = new_email
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_names(db: Session, user_id: UUID, first_name: str | None, last_name: str | None) -> User | None:
    """Update the user's first and last names."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    if first_name is not None:
        db_user.first_name = first_name
    if last_name is not None:
        db_user.last_name = last_name

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Delete a user"""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True
