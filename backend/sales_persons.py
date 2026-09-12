"""Sales Person administration routes for the CRM backend."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from backend.auth import admin_user, password_hash
from backend.database import engine, users_table


router = APIRouter(prefix="/admin/sales-persons", tags=["sales-persons"])


class SalesPersonInput(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str
    phone: str | None = None
    password: str
    confirm_password: str
    status: int


class SalesPersonUpdate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: str
    phone: str | None = None
    status: int


class SalesPersonResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str | None
    email: str
    phone: str | None
    status: int


def _sales_person_response(row: Any) -> dict[str, Any]:
    return SalesPersonResponse(
        user_id=row["user_id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        phone=row["phone"],
        status=row["status"],
    ).model_dump(mode="json")


@router.get("")
def admin_sales_persons(
    _user: dict[str, Any] = Depends(admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50),
) -> dict[str, Any]:
    """Return SALES_AGENT users from the public.users table."""
    statement = (
        select(
            users_table.c.user_id,
            users_table.c.first_name,
            users_table.c.last_name,
            users_table.c.email,
            users_table.c.phone,
            users_table.c.status,
        )
        .where(
            users_table.c.user_type_id == 3,
            users_table.c.status.in_((1, 2)),
        )
        .order_by(users_table.c.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_statement = select(users_table.c.user_id).where(
        users_table.c.user_type_id == 3,
        users_table.c.status.in_((1, 2)),
    )
    with engine.connect() as connection:
        rows = connection.execute(statement).mappings().all()
        total_count = len(connection.execute(count_statement).all())
    total_pages = (total_count + page_size - 1) // page_size
    return {
        "sales_persons": [
            _sales_person_response(row)
            for row in rows
        ],
        "current_page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total_pages > 0,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_admin_sales_person(
    sales_person: SalesPersonInput,
    user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Create a SALES_AGENT user owned by the current administrator."""
    first_name = sales_person.first_name.strip()
    last_name = (
        sales_person.last_name.strip() if sales_person.last_name else None
    )
    email = sales_person.email.strip().lower()
    phone = sales_person.phone.strip() if sales_person.phone else None
    if not first_name:
        raise HTTPException(status_code=422, detail="First name is required")
    if (
        not email
        or "@" not in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise HTTPException(status_code=422, detail="Invalid email address")
    if not sales_person.password:
        raise HTTPException(status_code=422, detail="Password is required")
    if sales_person.password != sales_person.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    if sales_person.status not in (1, 2):
        raise HTTPException(
            status_code=422, detail="Invalid sales person status")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    values = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "password": password_hash.hash(sales_person.password),
        "user_type_id": 3,
        "status": sales_person.status,
        "created_at": now,
        "updated_at": now,
        "created_by": user["user_id"],
        "updated_by": user["user_id"],
    }
    with engine.begin() as connection:
        if connection.execute(
            select(users_table.c.user_id).where(users_table.c.email == email)
        ).first() is not None:
            raise HTTPException(status_code=409, detail="Email already exists")
        try:
            result = connection.execute(users_table.insert().values(**values))
        except IntegrityError as error:
            raise HTTPException(
                status_code=409, detail="Email already exists") from error
        user_id = int(result.inserted_primary_key[0])

    return {"sales_person": _sales_person_response({
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "status": sales_person.status,
    })}


@router.get("/{user_id}")
def get_admin_sales_person(
    user_id: int,
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Return one SALES_AGENT without exposing its password."""
    statement = (
        select(
            users_table.c.user_id,
            users_table.c.first_name,
            users_table.c.last_name,
            users_table.c.email,
            users_table.c.phone,
            users_table.c.status,
        )
        .where(
            users_table.c.user_id == user_id,
            users_table.c.user_type_id == 3,
        )
    )
    with engine.connect() as connection:
        row = connection.execute(statement).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    return {"sales_person": _sales_person_response(row)}


@router.patch("/{user_id}")
def update_admin_sales_person(
    user_id: int,
    sales_person: SalesPersonUpdate,
    user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Update one SALES_AGENT without changing its password or role."""
    first_name = sales_person.first_name.strip()
    last_name = (
        sales_person.last_name.strip() if sales_person.last_name else None
    )
    email = sales_person.email.strip().lower()
    phone = sales_person.phone.strip() if sales_person.phone else None
    if not first_name:
        raise HTTPException(status_code=422, detail="First name is required")
    if (
        not email
        or "@" not in email
        or email.startswith("@")
        or email.endswith("@")
    ):
        raise HTTPException(status_code=422, detail="Invalid email address")
    if sales_person.status not in (1, 2):
        raise HTTPException(
            status_code=422, detail="Invalid sales person status")

    with engine.begin() as connection:
        target = connection.execute(
            select(users_table.c.user_id).where(
                users_table.c.user_id == user_id,
                users_table.c.user_type_id == 3,
            )
        ).first()
        if target is None:
            raise HTTPException(
                status_code=404, detail="Sales person not found")
        duplicate = connection.execute(
            select(users_table.c.user_id).where(
                users_table.c.email == email,
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
                    users_table.c.user_type_id == 3,
                )
                .values(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    status=sales_person.status,
                    updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    updated_by=user["user_id"],
                )
            )
        except IntegrityError as error:
            raise HTTPException(
                status_code=409, detail="Email already exists") from error
        if result.rowcount != 1:
            raise HTTPException(
                status_code=404, detail="Sales person not found")
        row = connection.execute(
            select(users_table).where(users_table.c.user_id == user_id)
        ).mappings().one()
    return {"sales_person": _sales_person_response(row)}


@router.delete("/{user_id}")
def delete_admin_sales_person(
    user_id: int,
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Soft-delete one SALES_AGENT user for an administrator."""
    with engine.begin() as connection:
        result = connection.execute(
            update(users_table)
            .where(
                users_table.c.user_id == user_id,
                users_table.c.user_type_id == 3,
            )
            .values(
                status=0,
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                updated_by=_user["user_id"],
            )
        )
        if result.rowcount != 1:
            raise HTTPException(
                status_code=404, detail="Sales person not found")
    return {"deleted": True, "user_id": user_id}
