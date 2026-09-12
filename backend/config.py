"""Backend configuration loaded from environment variables."""

import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL


load_dotenv()


def database_url() -> str:
    """Build the SQLAlchemy PostgreSQL URL for the existing test database."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    user = os.getenv("META_TEST_DB_USER", "postgres")
    password = os.getenv("META_TEST_DB_PASSWORD", "")
    host = os.getenv("META_TEST_DB_HOST", "127.0.0.1")
    port = os.getenv("META_TEST_DB_PORT", "5432")
    name = os.getenv("META_TEST_DB_NAME", "meta_lead_test_db")
    return URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=name,
    ).render_as_string(hide_password=False)


def cors_origins() -> list[str]:
    """Return configured browser origins for the frontend."""
    value = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001",
    )
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def jwt_secret_key() -> str:
    """Return the required signing key without exposing it to the frontend."""
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return secret


def jwt_access_token_minutes() -> int:
    """Return the access token lifetime in minutes."""
    return int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60"))
