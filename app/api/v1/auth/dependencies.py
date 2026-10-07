from functools import lru_cache
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status, Header
from jwt import PyJWKClient

from app.config import settings
from app.db.database import get_db
from app.db.user import (
    get_user_by_auth_id,
    create_user,
    update_user_email,
    update_user_names,
    UserRole,
    UserCreate,
    UserResponse,
)
from sqlalchemy.orm import Session


MANAGER_ROLES = frozenset({UserRole.ADMINISTRATOR, UserRole.COORDINATOR})


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=4)
def _jwks_client(supabase_url: str) -> PyJWKClient:
    """One client per Supabase project so the fetched JWKS is cached across requests."""
    return PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")


def extract_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise _credentials_exception()

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise _credentials_exception()

    return parts[1]


def decode_token(token: str = Depends(extract_token)) -> dict:
    """Verify a Supabase access token and return its claims."""
    try:
        algorithm = jwt.get_unverified_header(token).get("alg")

        if algorithm == "ES256":
            if not settings.supabase_url:
                raise HTTPException(status_code=500, detail="Supabase URL not configured")

            supabase_url = settings.supabase_url.rstrip("/")
            signing_key = _jwks_client(supabase_url).get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
                issuer=f"{supabase_url}/auth/v1",
            )
        else:
            secret = settings.supabase_jwt_secret
            if not secret:
                raise HTTPException(status_code=500, detail="JWT secret not configured")
            payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise _credentials_exception()

    if not payload.get("sub"):
        raise _credentials_exception()
    return payload


def get_current_user(
    claims: dict = Depends(decode_token),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Return the local user for a verified token. Read-only: the user must already be synced."""
    user = get_user_by_auth_id(db, claims["sub"])
    if not user:
        raise _credentials_exception()
    return UserResponse.model_validate(user)


def sync_current_user(
    claims: dict = Depends(decode_token),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create or refresh the local user from token claims. Only used by POST /auth/sync-user."""
    auth_id = claims["sub"]
    email = claims.get("email")
    metadata = claims.get("user_metadata") or {}
    first_name = claims.get("first_name") or metadata.get("first_name")
    last_name = claims.get("last_name") or metadata.get("last_name")

    user = get_user_by_auth_id(db, auth_id)
    if not user:
        user = create_user(
            db,
            UserCreate(auth_id=auth_id, email=email, first_name=first_name, last_name=last_name),
        )
    else:
        if email and user.email != email:
            user = update_user_email(db, user.id, email)
        if (first_name is not None and user.first_name != first_name) or (last_name is not None and user.last_name != last_name):
            user = update_user_names(db, user.id, first_name, last_name)
    return UserResponse.model_validate(user)


def get_optional_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> UserResponse | None:
    """Return the authenticated user when present, without requiring login."""
    if not authorization:
        return None
    try:
        return get_current_user(decode_token(extract_token(authorization)), db)
    except HTTPException:
        return None


def allow_roles(*allowed_roles: UserRole, detail: str = "Insufficient permissions"):
    """Create a dependency that requires the current user to have one of the allowed roles."""
    def dependency(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return current_user
    return dependency


def disallowed_roles(*disallowed_roles: UserRole, detail: str = "Insufficient permissions"):
    """Create a dependency that requires the current user to NOT have any of the disallowed roles."""
    def dependency(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role in disallowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return current_user
    return dependency


def require_manager(detail: str = "Insufficient permissions"):
    """Dependency requiring a coordinator or administrator."""
    return allow_roles(*MANAGER_ROLES, detail=detail)


def require_confirmed(detail: str = "Insufficient permissions"):
    """Dependency requiring any role other than applicant."""
    return disallowed_roles(UserRole.APPLICANT, detail=detail)


def is_manager(user: UserResponse) -> bool:
    return user.role in MANAGER_ROLES


def is_owner_or_role(
    user: UserResponse,
    owner_id: UUID | None,
    roles: frozenset[UserRole] = MANAGER_ROLES,
) -> bool:
    return user.role in roles or (owner_id is not None and owner_id == user.id)


def ensure_owner_or_role(
    user: UserResponse,
    owner_id: UUID | None,
    detail: str,
    roles: frozenset[UserRole] = MANAGER_ROLES,
) -> None:
    """Raise 403 unless the user owns the resource or holds one of the given roles."""
    if not is_owner_or_role(user, owner_id, roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
