"""Mock WhatsApp lead import routes."""

from datetime import datetime, timezone
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import psycopg

from backend.auth import admin_user
from backend.lead_assignment import assign_lead_and_notify


router = APIRouter(prefix="/admin/whatsapp", tags=["whatsapp-import"])


class WhatsAppLeadImport(BaseModel):
    lead_id: str
    full_name: str
    email: str
    phone: str


def _validate_lead(lead: WhatsAppLeadImport) -> dict[str, str]:
    lead_id = lead.lead_id.strip()
    full_name = lead.full_name.strip()
    email = lead.email.strip().lower()
    phone = lead.phone.strip()
    if not lead_id or not full_name or not email or not phone:
        raise HTTPException(
            status_code=422,
            detail="lead_id, full_name, email, and phone are required",
        )
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="Invalid email address")
    if not any(character.isdigit() for character in phone):
        raise HTTPException(status_code=422, detail="Invalid phone number")
    return {
        "lead_id": lead_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
    }


@router.post("/import")
def import_whatsapp_lead(
    lead: WhatsAppLeadImport,
    _user: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    """Validate and import one mock WhatsApp lead into public.leads."""
    values = _validate_lead(lead)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        with psycopg.connect(
            host=os.getenv("META_TEST_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("META_TEST_DB_PORT", "5432")),
            dbname=os.getenv("META_TEST_DB_NAME", "meta_lead_test_db"),
            user=os.getenv("META_TEST_DB_USER", "postgres"),
            password=os.getenv("META_TEST_DB_PASSWORD", ""),
        ) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT lead_id
                        FROM public.leads
                        WHERE meta_leadgen_id = %(lead_id)s
                        """,
                        {"lead_id": values["lead_id"]},
                    )
                    if cursor.fetchone() is not None:
                        return {
                            "status": "duplicate",
                            "message": "WhatsApp lead already imported.",
                            "lead_id": values["lead_id"],
                        }

                    cursor.execute(
                        """
                        SELECT market_source_id
                        FROM public.market_sources
                        WHERE name = 'WhatsApp'
                        """,
                        (),
                    )
                    source = cursor.fetchone()
                    if source is None:
                        raise HTTPException(
                            status_code=503,
                            detail="WhatsApp market source is not configured",
                        )
                    cursor.execute(
                        """
                        INSERT INTO public.leads
                            (name, email, phone, source, market_source_id,
                             meta_leadgen_id, created_at, updated_at)
                        VALUES (%(name)s, %(email)s, %(phone)s, 'WhatsApp',
                                %(market_source_id)s, %(meta_leadgen_id)s,
                                %(created_at)s, %(updated_at)s)
                        RETURNING lead_id
                        """,
                        {
                            "name": values["full_name"],
                            "email": values["email"],
                            "phone": values["phone"],
                            "market_source_id": source[0],
                            "meta_leadgen_id": values["lead_id"],
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                    database_lead_id = cursor.fetchone()[0]
                    assign_lead_and_notify(cursor, database_lead_id)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except psycopg.errors.UniqueViolation as error:
        raise HTTPException(
            status_code=409,
            detail="WhatsApp lead was already imported",
        ) from error
    except psycopg.Error as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to import WhatsApp lead",
        ) from error
    return {
        "status": "imported",
        "message": "WhatsApp lead imported successfully.",
        "lead_id": values["lead_id"],
        "database_lead_id": database_lead_id,
    }
