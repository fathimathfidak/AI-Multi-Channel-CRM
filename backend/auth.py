"""Authentication services for the existing users table."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import insert, select

from backend.config import jwt_access_token_minutes, jwt_secret_key
from backend.database import engine, user_types_table, users_table


ADMIN_USER_TYPE_ID = 1
ACTIVE_STATUS = 1
password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    """Return only fields safe to send to a client."""
    return {
        "user_id": user["user_id"],
        "first_name": user["first_name"],
        "last_name": user.get("last_name"),
        "email": user["email"],
        "phone": user.get("phone"),
        "user_type_id": user["user_type_id"],
        "status": user["status"],
    }


def find_user_by_email(email: str) -> dict[str, Any] | None:
    """Load one user by normalized email."""
    statement = (
        select(users_table)
        .join(user_types_table,
              users_table.c.user_type_id == user_types_table.c.user_type_id)
        .where(users_table.c.email == email)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).mappings().first()
    return dict(row) if row else None


def find_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Load one user by primary key for token validation."""
    statement = (
        select(users_table)
        .join(user_types_table,
              users_table.c.user_type_id == user_types_table.c.user_type_id)
        .where(users_table.c.user_id == user_id)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).mappings().first()
    return dict(row) if row else None


def create_access_token(user: dict[str, Any]) -> str:
    """Create a short-lived JWT containing only authorization claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["user_id"]),
        "user_type_id": user["user_type_id"],
        "iat": now,
        "exp": now + timedelta(minutes=jwt_access_token_minutes()),
    }
    return jwt.encode(payload, jwt_secret_key(), algorithm="HS256")


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Authenticate an active user with a one-way password hash."""
    user = find_user_by_email(email.strip().lower())
    if not user or user["status"] != ACTIVE_STATUS:
        return None
    if not password_hash.verify(password, user["password"]):
        return None
    return user


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Decode a bearer token and re-check the user's current database status."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            jwt_secret_key(),
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError, RuntimeError) as error:
        raise unauthorized from error

    user = find_user_by_id(user_id)
    if not user or user["status"] != ACTIVE_STATUS:
        raise unauthorized
    return user


def admin_user(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    """Require an active ADMIN user."""
    if user["user_type_id"] != ADMIN_USER_TYPE_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


def create_first_admin(
    *,
    first_name: str,
    last_name: str | None,
    email: str,
    phone: str | None,
    password: str,
) -> int:
    """Insert the first admin only when the database has no ADMIN users."""
    with engine.begin() as connection:
        existing_admin = connection.execute(
            select(users_table.c.user_id)
            .where(users_table.c.user_type_id == ADMIN_USER_TYPE_ID)
            .limit(1)
        ).first()
        if existing_admin:
            raise ValueError("An ADMIN user already exists")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        result = connection.execute(
            insert(users_table).values(
                first_name=first_name,
                last_name=last_name,
                email=email.strip().lower(),
                phone=phone,
                password=password_hash.hash(password),
                user_type_id=ADMIN_USER_TYPE_ID,
                status=ACTIVE_STATUS,
                created_at=now,
                updated_at=now,
                created_by=None,
                updated_by=None,
            )
        )
        return int(result.inserted_primary_key[0])
