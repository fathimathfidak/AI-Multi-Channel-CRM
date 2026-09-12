"""Small standalone test for reading Meta Lead Ads form leads."""

import argparse
from datetime import datetime, timezone
import getpass
import logging
import os
import sys
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
import psycopg
import requests
import uvicorn
from dotenv import load_dotenv

from backend.lead_assignment import assign_lead_and_notify


load_dotenv()

# Meta's Graph API endpoint for reading leads from a specific lead form.
GRAPH_API_URL = "https://graph.facebook.com"
TEST_DATABASE_NAME = "meta_lead_test_db"
REQUEST_TIMEOUT_SECONDS = 30
app = FastAPI(title="Meta Lead Test Webhook")
logger = logging.getLogger("meta_lead_test")

# These are common field names used by lead forms. The parser below recognizes
# them while still printing every field returned by Meta.
COMMON_FIELD_NAMES = {
    "full_name",
    "first_name",
    "last_name",
    "email",
    "phone_number",
    "phone",
    "message",
    "enquiry",
    "question",
    "location",
}


class MetaLeadAPIError(Exception):
    """Raised when Meta returns an error or an unusable response."""


def parse_common_fields(
    field_data: list[dict[str, Any]],
) -> dict[str, list[Any]]:
    """Return values for common lead field names found in Meta's response."""
    parsed_fields: dict[str, list[Any]] = {}

    for field in field_data:
        field_name = field.get("name")
        if field_name in COMMON_FIELD_NAMES:
            field_values = field.get("values", [])
            parsed_fields[field_name] = field_values

    return parsed_fields


def _read_response(response: requests.Response) -> dict[str, Any]:
    """Convert JSON and turn Meta errors into a clear exception."""
    try:
        response_data = response.json()
    except ValueError as error:
        raise MetaLeadAPIError(
            f"Meta returned invalid JSON (HTTP {response.status_code})."
        ) from error

    if not isinstance(response_data, dict):
        raise MetaLeadAPIError("Meta returned JSON in an unexpected format.")

    # Meta may include an error object, including in a response with HTTP 200.
    if "error" in response_data:
        meta_error = response_data["error"]
        if isinstance(meta_error, dict):
            message = meta_error.get("message", "Unknown Meta API error")
            error_code = meta_error.get("code")
            code_text = (
                f" (code {error_code})" if error_code is not None else ""
            )
            raise MetaLeadAPIError(f"Meta API error{code_text}: {message}")
        raise MetaLeadAPIError(f"Meta API error: {meta_error}")

    if not response.ok:
        raise MetaLeadAPIError(
            f"Meta returned HTTP {response.status_code}: "
            f"{response.reason or 'request failed'}"
        )

    return response_data


def get_form_leads(form_id: str, access_token: str) -> list[dict[str, Any]]:
    """Retrieve all leads for a Meta lead form, following pagination links."""
    # The access token is sent to Meta, but is never printed or included
    # in errors.
    next_url: str | None = f"{GRAPH_API_URL}/{form_id}/leads"
    request_params: dict[str, str] | None = {
        "access_token": access_token,
        "fields": "id,created_time,field_data,form_id,page_id,campaign_id",
    }
    all_leads: list[dict[str, Any]] = []

    while next_url:
        try:
            response = requests.get(
                next_url,
                params=request_params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            raise MetaLeadAPIError(
                f"Could not connect to Meta: {error}"
            ) from error

        response_data = _read_response(response)
        leads = response_data.get("data", [])
        if not isinstance(leads, list):
            raise MetaLeadAPIError(
                "Meta returned lead data in an unexpected format."
            )
        all_leads.extend(lead for lead in leads if isinstance(lead, dict))

        # Meta's next URL already contains the information needed for
        # the next page.
        next_url = response_data.get("paging", {}).get("next")
        request_params = None

    return all_leads


def get_lead_by_id(leadgen_id: str, access_token: str) -> dict[str, Any]:
    """Retrieve one existing lead; this never creates leads."""
    lead_url = f"{GRAPH_API_URL}/{leadgen_id}"
    try:
        response = requests.get(
            lead_url,
            params={
                "access_token": access_token,
                "fields": (
                    "id,created_time,field_data,form_id,page_id,campaign_id"
                ),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise MetaLeadAPIError(
            f"Could not connect to Meta while reading the lead: {error}"
        ) from error

    lead = _read_response(response)
    if not lead.get("id"):
        raise MetaLeadAPIError("Meta returned a lead without an ID.")
    return lead


def get_form_page_id(form_id: str, access_token: str) -> str:
    """Retrieve the Page ID belonging to the lead form."""
    form_url = f"{GRAPH_API_URL}/{form_id}"

    try:
        response = requests.get(
            form_url,
            params={"access_token": access_token, "fields": "page_id"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as error:
        raise MetaLeadAPIError(
            f"Could not connect to Meta while reading the form: {error}"
        ) from error

    form_data = _read_response(response)
    page_id = form_data.get("page_id")
    if not page_id:
        raise MetaLeadAPIError("Meta did not return a Page ID for this form.")

    return str(page_id)


def get_field_value(
    field_data: list[dict[str, Any]],
    field_names: set[str],
) -> str:
    """Find the first value for one of the requested field names."""
    normalized_names = {
        "".join(character for character in name if character.isalnum())
        for name in field_names
    }

    for field in field_data:
        field_name = str(field.get("name", "")).strip().lower()
        normalized_field_name = "".join(
            character for character in field_name if character.isalnum()
        )
        if normalized_field_name in normalized_names:
            values = field.get("values", [])
            if isinstance(values, list) and values:
                return ", ".join(map(str, values))

    return "Not provided"


def get_custom_interest(field_data: list[dict[str, Any]]) -> str:
    """Extract the custom interest answer, including numeric Meta keys."""
    custom_interest = get_field_value(
        field_data,
        {
            "what are you interested in?",
            "what_are_you_interested_in",
            "enquiry",
            "question",
        },
    )
    if custom_interest != "Not provided":
        return custom_interest

    standard_names = {
        "".join(character for character in name if character.isalnum())
        for name in COMMON_FIELD_NAMES
    }
    for field in field_data:
        field_name = str(field.get("name", "")).strip().lower()
        normalized_name = "".join(
            character for character in field_name if character.isalnum()
        )
        values = field.get("values", [])
        if normalized_name not in standard_names and values:
            return ", ".join(map(str, values))

    return "Not provided"


def normalize_lead(
    lead: dict[str, Any],
    page_id: str,
    form_id: str,
) -> dict[str, str | None]:
    """Convert one Meta lead response into the database column structure."""
    field_data = lead.get("field_data", [])
    if not isinstance(field_data, list):
        field_data = []

    full_name = get_field_value(field_data, {"full_name"})
    if full_name == "Not provided":
        full_name = " ".join(
            part for part in (
                get_field_value(field_data, {"first_name"}),
                get_field_value(field_data, {"last_name"}),
            )
            if part != "Not provided"
        ) or None

    created_at = lead.get("created_time")
    if isinstance(created_at, str):
        created_at = created_at.replace("Z", "+00:00")

    campaign_id = lead.get("campaign_id")
    if campaign_id is not None:
        campaign_id = str(campaign_id)

    location = get_field_value(field_data, {"location"})
    if location == "Not provided":
        location = None

    return {
        "leadgen_id": str(lead.get("id", "")),
        "page_id": page_id,
        "form_id": str(lead.get("form_id") or form_id),
        "name": full_name,
        "phone": nullable_meta_field(
            get_field_value(field_data, {"phone_number", "phone"})
        ),
        "email": nullable_meta_field(get_field_value(field_data, {"email"})),
        "enquiry": nullable_meta_field(get_custom_interest(field_data)),
        "created_at": created_at,
        "campaign_id": campaign_id,
        "location": location,
    }


def nullable_meta_field(value: str | None) -> str | None:
    """Convert the parser's display sentinel into a database NULL."""
    return None if value in (None, "Not provided") else value


def save_lead_to_database(lead_data: dict[str, str | None]) -> bool:
    """Insert one lead into the separate test database using parameters."""
    database_user = os.getenv("META_TEST_DB_USER", "postgres")
    database_host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    database_port = os.getenv("META_TEST_DB_PORT", "5432")
    database_name = os.getenv("META_TEST_DB_NAME", TEST_DATABASE_NAME)
    database_password = getpass.getpass(
        "PostgreSQL password for the standalone test database: "
    )

    insert_sql = """
        INSERT INTO meta_leads
            (
                leadgen_id, page_id, form_id, name,
                phone, email, enquiry, created_at
            )
        VALUES (%(leadgen_id)s, %(page_id)s, %(form_id)s, %(name)s,
                %(phone)s, %(email)s, %(enquiry)s, %(created_at)s)
        ON CONFLICT (leadgen_id) DO NOTHING
    """
    try:
        with psycopg.connect(
            host=database_host,
            port=database_port,
            dbname=database_name,
            user=database_user,
            password=database_password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_sql, lead_data)
                return cursor.rowcount == 1
    except psycopg.Error as error:
        raise MetaLeadAPIError(
            f"Could not save the lead to PostgreSQL: {error}"
        ) from error


def save_lead_with_password(
    lead_data: dict[str, str | None],
    database_password: str,
) -> bool:
    """Save a lead without prompting, for use by the webhook server."""
    database_user = os.getenv("META_TEST_DB_USER", "postgres")
    database_host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    database_port = os.getenv("META_TEST_DB_PORT", "5432")
    database_name = os.getenv("META_TEST_DB_NAME", TEST_DATABASE_NAME)
    insert_sql = """
        INSERT INTO meta_leads
            (
                leadgen_id, page_id, form_id, name,
                phone, email, enquiry, created_at
            )
        VALUES (%(leadgen_id)s, %(page_id)s, %(form_id)s, %(name)s,
                %(phone)s, %(email)s, %(enquiry)s, %(created_at)s)
        ON CONFLICT (leadgen_id) DO NOTHING
    """
    try:
        with psycopg.connect(
            host=database_host,
            port=database_port,
            dbname=database_name,
            user=database_user,
            password=database_password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_sql, lead_data)
                return cursor.rowcount == 1
    except psycopg.Error as error:
        raise MetaLeadAPIError(
            "Could not save the lead to the standalone PostgreSQL database."
        ) from error


def save_crm_lead_with_password(
    lead_data: dict[str, str | None],
    database_password: str,
) -> bool:
    """Insert a Meta lead into public.leads without duplicating it."""
    database_user = os.getenv("META_TEST_DB_USER", "postgres")
    database_host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    database_port = os.getenv("META_TEST_DB_PORT", "5432")
    database_name = os.getenv("META_TEST_DB_NAME", TEST_DATABASE_NAME)
    created_at = lead_data.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    if not isinstance(created_at, datetime):
        created_at = datetime.now(timezone.utc)
    if created_at.tzinfo is not None:
        created_at = created_at.astimezone(timezone.utc).replace(tzinfo=None)

    def nullable(value: str | None) -> str | None:
        return None if value in (None, "Not provided") else value

    insert_sql = """
        INSERT INTO public.leads
            (
                name, email, phone, source, message, campaign_id, location,
                priority_id, market_source_id, meta_leadgen_id,
                created_at, updated_at
            )
        SELECT
            %(name)s, %(email)s, %(phone)s, 'Meta Ads', %(message)s,
            %(campaign_id)s,
            %(location)s, NULL, market_source_id, %(meta_leadgen_id)s,
            %(created_at)s, %(updated_at)s
        FROM public.market_sources
        WHERE name = 'Meta Ads'
        ON CONFLICT (meta_leadgen_id) DO NOTHING
        RETURNING lead_id
    """
    values = {
        "name": nullable(lead_data.get("name")),
        "email": nullable(lead_data.get("email")),
        "phone": nullable(lead_data.get("phone")),
        "message": nullable(lead_data.get("enquiry")),
        "campaign_id": nullable(lead_data.get("campaign_id")),
        "location": nullable(lead_data.get("location")),
        "meta_leadgen_id": lead_data["leadgen_id"],
        "created_at": created_at,
        "updated_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    try:
        with psycopg.connect(
            host=database_host,
            port=database_port,
            dbname=database_name,
            user=database_user,
            password=database_password,
        ) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(insert_sql, values)
                    if cursor.rowcount != 1:
                        return False
                    lead_id = cursor.fetchone()[0]
                    assign_lead_and_notify(cursor, lead_id)
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise
    except psycopg.Error as error:
        raise MetaLeadAPIError(
            "Could not save the lead to public.leads."
        ) from error


def select_saved_lead(
    leadgen_id: str,
    database_password: str,
) -> tuple[Any, ...] | None:
    """Read one saved row without changing the database."""
    database_user = os.getenv("META_TEST_DB_USER", "postgres")
    database_host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    database_port = os.getenv("META_TEST_DB_PORT", "5432")
    database_name = os.getenv("META_TEST_DB_NAME", TEST_DATABASE_NAME)
    select_sql = """
         SELECT leadgen_id, page_id, form_id, name, phone, email,
             enquiry, created_at
        FROM meta_leads
        WHERE leadgen_id = %s
    """
    try:
        with psycopg.connect(
            host=database_host,
            port=database_port,
            dbname=database_name,
            user=database_user,
            password=database_password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(select_sql, (leadgen_id,))
                return cursor.fetchone()
    except psycopg.Error as error:
        raise MetaLeadAPIError(
            "Could not verify the saved lead in the standalone database."
        ) from error


def print_saved_lead(leadgen_id: str) -> None:
    """Run a read-only query and print the saved lead fields."""
    database_user = os.getenv("META_TEST_DB_USER", "postgres")
    database_host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    database_port = os.getenv("META_TEST_DB_PORT", "5432")
    database_password = getpass.getpass(
        "PostgreSQL password for read-only verification: "
    )
    select_sql = """
         SELECT leadgen_id, page_id, form_id, name, phone, email,
             enquiry, created_at
        FROM meta_leads
        WHERE leadgen_id = %s
    """
    try:
        with psycopg.connect(
            host=database_host,
            port=database_port,
            dbname=TEST_DATABASE_NAME,
            user=database_user,
            password=database_password,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(select_sql, (leadgen_id,))
                saved_lead = cursor.fetchone()
    except psycopg.Error as error:
        raise MetaLeadAPIError(
            f"Could not verify the saved lead in PostgreSQL: {error}"
        ) from error

    if saved_lead is None:
        raise MetaLeadAPIError("The lead was not found in meta_leads.")

    labels = (
        "Lead ID",
        "Page ID",
        "Form ID",
        "Name",
        "Phone",
        "Email",
        "Enquiry",
        "Created at",
    )
    for label, value in zip(labels, saved_lead):
        print(f"{label}: {value}")


def _webhook_lead_events(
    payload: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """Extract (leadgen_id, page_id, form_id) from Meta's webhook payload."""
    events: list[tuple[str, str, str]] = []
    entries = payload.get("entry", [])
    if not isinstance(entries, list):
        logger.warning("Invalid Meta webhook payload: entry is not a list")
        return events
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        page_id = str(entry.get("id", ""))
        changes = entry.get("changes", [])
        if not isinstance(changes, list):
            logger.warning(
                "Invalid Meta webhook payload: changes is not a list")
            continue
        for change in changes:
            value = change.get("value", {}) if isinstance(change, dict) else {}
            leadgen_id = value.get("leadgen_id")
            if leadgen_id:
                events.append((
                    str(leadgen_id),
                    page_id,
                    str(value.get("form_id", "")),
                ))
            else:
                logger.warning("Meta webhook event is missing leadgen_id")
    return events


@app.get("/webhook")
def verify_webhook(request: Request) -> PlainTextResponse:
    """Verify Meta's webhook subscription using the configured verify token."""
    query = request.query_params
    expected_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN")
    challenge = query.get("hub.challenge")
    if (
        query.get("hub.mode") == "subscribe"
        and expected_token
        and query.get("hub.verify_token") == expected_token
        and challenge is not None
    ):
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, Any]:
    """Receive leadgen events, retrieve each lead from Meta, and save it."""
    access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
    database_password = os.getenv("META_TEST_DB_PASSWORD")
    if not access_token or not database_password:
        raise HTTPException(
            status_code=500,
            detail="Webhook server configuration is incomplete",
        )

    try:
        payload = await request.json()
    except ValueError as error:
        logger.warning("Invalid Meta webhook JSON payload")
        raise HTTPException(
            status_code=400, detail="Invalid JSON payload") from error

    if not isinstance(payload, dict):
        logger.warning("Invalid Meta webhook payload type: %s",
                       type(payload).__name__)
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    events = _webhook_lead_events(payload)
    if not events:
        return {"received": True, "processed": 0}

    processed = 0
    for leadgen_id, webhook_page_id, webhook_form_id in events:
        logger.info("Meta lead webhook received: leadgen_id=%s", leadgen_id)
        try:
            if not leadgen_id:
                logger.warning("Meta webhook event is missing leadgen_id")
                continue
            lead = get_lead_by_id(leadgen_id, access_token)
            page_id = webhook_page_id or str(lead.get("page_id", ""))
            lead_data = normalize_lead(
                {**lead, "form_id": webhook_form_id},
                page_id,
                webhook_form_id,
            )
            logger.info(
                "Meta lead retrieved: leadgen_id=%s form_id=%s",
                leadgen_id,
                webhook_form_id,
            )
            crm_inserted = save_crm_lead_with_password(
                lead_data,
                database_password,
            )
            logger.info(
                "CRM lead %s: leadgen_id=%s",
                "saved" if crm_inserted else "already existed",
                leadgen_id,
            )
            processed += 1
        except Exception as error:
            logger.exception("Meta lead webhook processing failed: %s", error)
            raise HTTPException(
                status_code=502,
                detail="Unable to retrieve or save Meta lead",
            ) from error

    return {"received": True, "processed": processed}


def print_lead(lead: dict[str, Any]) -> None:
    """Print the requested details from one lead."""
    print(f"Lead ID / leadgen_id: {lead.get('id', 'Not provided')}")
    print(f"Created time: {lead.get('created_time', 'Not provided')}")
    print(f"Form ID: {lead.get('form_id', 'Not provided')}")

    field_data = lead.get("field_data", [])
    if not isinstance(field_data, list):
        print("Field data: Not provided")
        return

    # Read standard fields and the custom question using their
    # Meta field names.
    full_name = get_field_value(field_data, {"full_name"})
    first_name = get_field_value(field_data, {"first_name"})
    last_name = get_field_value(field_data, {"last_name"})
    if full_name == "Not provided":
        full_name = " ".join(
            part for part in (first_name, last_name)
            if part != "Not provided"
        ) or "Not provided"

    print(f"Full Name: {full_name}")
    print(
        "Phone Number: "
        + get_field_value(field_data, {"phone_number", "phone"})
    )
    print(f"Email: {get_field_value(field_data, {'email'})}")
    print(f"What are you interested in?: {get_custom_interest(field_data)}")

    if not field_data:
        print("Field data: None")
        return


def main() -> None:
    """Load settings, validate them, retrieve leads, and display results."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--webhook",
        action="store_true",
        help="Start the local FastAPI webhook server.",
    )
    args = parser.parse_args()
    if args.webhook:
        uvicorn.run(app, host="127.0.0.1", port=8000)
        return

    # Load variables from a local .env file into the process environment.
    load_dotenv()

    access_token = os.getenv("META_PAGE_ACCESS_TOKEN")
    form_id = os.getenv("META_LEAD_FORM_ID")

    # Stop before making a request when required settings are absent.
    missing_settings = []
    if not access_token:
        missing_settings.append("META_PAGE_ACCESS_TOKEN")
    if not form_id:
        missing_settings.append("META_LEAD_FORM_ID")

    if missing_settings:
        print(
            "Missing required environment variable(s): "
            + ", ".join(missing_settings)
        )
        print("Copy .env.example to .env and fill in the missing value(s).")
        sys.exit(1)

    try:
        page_id = get_form_page_id(form_id, access_token)
        leads = get_form_leads(form_id, access_token)
    except MetaLeadAPIError as error:
        print(f"Lead request failed: {error}")
        sys.exit(1)

    if not leads:
        print("No leads were returned for this form.")
        return

    lead = leads[0]
    lead_data = normalize_lead(lead, page_id, form_id)
    if not lead_data["leadgen_id"]:
        print("Lead request failed: Meta returned a lead without an ID.")
        sys.exit(1)

    try:
        inserted = save_lead_to_database(lead_data)
        print("Lead saved to meta_leads." if inserted else
              "Lead already exists in meta_leads; no duplicate inserted.")
        print_saved_lead(lead_data["leadgen_id"])
    except MetaLeadAPIError as error:
        print(f"Database operation failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
