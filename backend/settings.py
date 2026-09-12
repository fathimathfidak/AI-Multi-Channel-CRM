"""Administrator settings routes for the authenticated user's profile."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from backend.auth import admin_user, password_hash
from backend.database import engine, users_table


router = APIRouter(prefix="/admin/settings", tags=["settings"])


class AdminProfileUpdate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str
    phone: str | None = None


class AdminProfileResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str | None
    email: str
    phone: str | None


class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


def _profile_response(row: Any) -> dict[str, Any]:
    return AdminProfileResponse(
        user_id=row["user_id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        phone=row["phone"],
    ).model_dump(mode="json")


def _profile_values(profile: AdminProfileUpdate) -> dict[str, str | None]:
    first_name = profile.first_name.strip()
    email = profile.email.strip().lower()
    if not first_name:
        raise HTTPException(status_code=422, detail="First name is required")
    if (
        not email
        or "@" not in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise HTTPException(status_code=422, detail="Invalid email address")
    return {
        "first_name": first_name,
        "last_name": profile.last_name.strip() if profile.last_name else None,
        "email": email,
        "phone": profile.phone.strip() if profile.phone else None,
    }


@router.get("/profile")
def get_admin_profile(
    user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Return only the authenticated administrator's profile fields."""
    statement = select(
        users_table.c.user_id,
        users_table.c.first_name,
        users_table.c.last_name,
        users_table.c.email,
        users_table.c.phone,
    ).where(users_table.c.user_id == user["user_id"])
    with engine.connect() as connection:
        row = connection.execute(statement).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    return {"profile": _profile_response(row)}


@router.patch("/profile")
def update_admin_profile(
    profile: AdminProfileUpdate,
    user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Update the authenticated administrator's editable profile fields."""
    values = _profile_values(profile)
    user_id = user["user_id"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with engine.begin() as connection:
        duplicate = connection.execute(
            select(users_table.c.user_id).where(
                users_table.c.email == values["email"],
                users_table.c.user_id != user_id,
            )
        ).first()
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="Email already exists")
        try:
            result = connection.execute(
                update(users_table)
                .where(
                    users_table.c.user_id == user_id,
                    users_table.c.user_type_id == 1,
                )
                .values(
                    **values,
                    updated_at=now,
                    updated_by=user_id,
                )
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=409, detail="Email already exists"
            ) from error
        if result.rowcount != 1:
            raise HTTPException(
                status_code=404, detail="Admin profile not found")
        row = connection.execute(
            select(
                users_table.c.user_id,
                users_table.c.first_name,
                users_table.c.last_name,
                users_table.c.email,
                users_table.c.phone,
            ).where(users_table.c.user_id == user_id)
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    return {"profile": _profile_response(row)}


@router.post("/change-password")
def change_admin_password(
    passwords: AdminPasswordChange,
    user: dict[str, Any] = Depends(admin_user),
) -> dict[str, str]:
    """Change the authenticated administrator's password."""
    if passwords.new_password != passwords.confirm_password:
        raise HTTPException(
            status_code=422,
            detail="New password and confirm password do not match.",
        )
    with engine.begin() as connection:
        row = connection.execute(
            select(users_table.c.password).where(
                users_table.c.user_id == user["user_id"],
                users_table.c.user_type_id == 1,
            )
        ).first()
        if row is None or not password_hash.verify(
            passwords.current_password, row[0]
        ):
            raise HTTPException(
                status_code=400, detail="Current password is incorrect."
            )
        result = connection.execute(
            update(users_table)
            .where(
                users_table.c.user_id == user["user_id"],
                users_table.c.user_type_id == 1,
            )
            .values(
                password=password_hash.hash(passwords.new_password),
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                updated_by=user["user_id"],
            )
        )
        if result.rowcount != 1:
            raise HTTPException(
                status_code=404, detail="Admin profile not found")
    return {"message": "Password successfully changed."}
