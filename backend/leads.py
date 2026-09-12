"""Lead administration routes for the CRM backend."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, func, select, update

from backend.auth import admin_user
from backend.database import (
    engine,
    leads_table,
    market_sources_table,
    priority_table,
)


router = APIRouter(prefix="/admin", tags=["leads"])


class LeadResponse(BaseModel):
    lead_id: int
    company: str | None
    name: str | None
    email: str | None
    phone: str | None
    source: str | None
    message: str | None
    campaign_id: str | None
    location: str | None
    priority_id: int | None
    priority: str | None
    market_source_id: int | None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    market_source_id: int | None = None
    message: str | None = None
    campaign_id: str | None = None
    location: str | None = None
    priority_id: int | None = None


@router.get("/leads")
def admin_leads(
    _user: dict[str, Any] = Depends(admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=50),
) -> dict[str, Any]:
    """Return the latest leads for an authenticated administrator."""
    count_statement = select(
        func.count(leads_table.c.lead_id),
    ).select_from(leads_table)
    lead_statement = (
        select(
            leads_table,
            market_sources_table.c.name.label("source_name"),
            priority_table.c.name.label("priority_name"),
        )
        .select_from(
            leads_table
            .outerjoin(
                market_sources_table,
                leads_table.c.market_source_id
                == market_sources_table.c.market_source_id,
            )
            .outerjoin(
                priority_table,
                leads_table.c.priority_id == priority_table.c.priority_id,
            )
        )
        .order_by(leads_table.c.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    with engine.connect() as connection:
        total_count = int(connection.execute(count_statement).scalar_one())
        rows = connection.execute(lead_statement).mappings().all()

    total_pages = (total_count + page_size - 1) // page_size
    return {
        "leads": [
            LeadResponse(
                **{
                    key: row[key]
                    for key in (
                        "lead_id",
                        "company",
                        "name",
                        "email",
                        "phone",
                        "message",
                        "campaign_id",
                        "location",
                        "priority_id",
                        "market_source_id",
                        "created_at",
                        "updated_at",
                    )
                },
                source=row["source_name"],
                priority=row["priority_name"],
            ).model_dump(mode="json")
            for row in rows
        ],
        "current_page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total_pages > 0,
    }


@router.get("/lead-options")
def admin_lead_options(
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, list[dict[str, Any]]]:
    """Return the existing source and priority choices for lead forms."""
    with engine.connect() as connection:
        sources = connection.execute(
            select(market_sources_table).order_by(
                market_sources_table.c.market_source_id,
            )
        ).mappings().all()
        priorities = connection.execute(
            select(priority_table).order_by(priority_table.c.priority_id)
        ).mappings().all()
    return {
        "market_sources": [dict(row) for row in sources],
        "priorities": [dict(row) for row in priorities],
    }


@router.patch("/leads/{lead_id}")
def update_admin_lead(
    lead_id: int,
    changes: LeadUpdate,
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Update editable fields on one CRM lead."""
    values = changes.model_dump(exclude_unset=True)
    if "market_source_id" in values and values["market_source_id"] is not None:
        source_exists = select(market_sources_table.c.market_source_id).where(
            market_sources_table.c.market_source_id
            == values["market_source_id"]
        )
        with engine.connect() as connection:
            if connection.execute(source_exists).first() is None:
                raise HTTPException(
                    status_code=422, detail="Invalid market source")
    if "priority_id" in values and values["priority_id"] is not None:
        priority_exists = select(priority_table.c.priority_id).where(
            priority_table.c.priority_id == values["priority_id"]
        )
        with engine.connect() as connection:
            if connection.execute(priority_exists).first() is None:
                raise HTTPException(status_code=422, detail="Invalid priority")

    values["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    with engine.begin() as connection:
        result = connection.execute(
            update(leads_table)
            .where(leads_table.c.lead_id == lead_id)
            .values(**values)
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=404, detail="Lead not found")
    return {"updated": True, "lead_id": lead_id}


@router.delete("/leads/{lead_id}")
def delete_admin_lead(
    lead_id: int,
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Delete one CRM lead for an authenticated administrator."""
    with engine.begin() as connection:
        result = connection.execute(
            delete(leads_table).where(leads_table.c.lead_id == lead_id)
        )
        if result.rowcount != 1:
            raise HTTPException(status_code=404, detail="Lead not found")
    return {"deleted": True, "lead_id": lead_id}
