from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt as jose_jwt
from jwt import PyJWKClient, decode as pyjwt_decode
from jwt.exceptions import InvalidTokenError, PyJWKClientError

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


def extract_token(authorization: Optional[str] = Header(None)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization:
        raise credentials_exception

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise credentials_exception

    return parts[1]


def get_current_user(
    token: str = Depends(extract_token),
    db: Session = Depends(get_db),
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_header = jose_jwt.get_unverified_header(token)
        algorithm = token_header.get("alg")

        if algorithm == "ES256":
            if not settings.supabase_url:
                raise HTTPException(status_code=500, detail="Supabase URL not configured")

            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
            payload = pyjwt_decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
            )
        else:
            secret = settings.supabase_jwt_secret
            if not secret:
                raise HTTPException(status_code=500, detail="JWT secret not configured")
            payload = jose_jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])

        auth_id = payload.get("sub")
        email = payload.get("email")
        first_name = payload.get("first_name") or payload.get("user_metadata", {}).get("first_name")
        last_name = payload.get("last_name") or payload.get("user_metadata", {}).get("last_name")
        if not auth_id:
            raise credentials_exception
    except (JWTError, InvalidTokenError, PyJWKClientError):
        raise credentials_exception

    user = get_user_by_auth_id(db, auth_id)
    if not user:
        user_in = UserCreate(
            auth_id=auth_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user = create_user(db, user_in)
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
        token = extract_token(authorization)
        return get_current_user(token, db)
    except HTTPException:
        return None


def allow_roles(*allowed_roles: UserRole):
    """Create a dependency that requires the current user to have one of the allowed roles."""
    def dependency(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return dependency


def disallowed_roles(*disallowed_roles: UserRole):
    """Create a dependency that requires the current user to NOT have any of the disallowed roles."""
    def dependency(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        if current_user.role in disallowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return dependency