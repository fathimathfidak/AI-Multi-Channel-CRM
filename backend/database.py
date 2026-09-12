"""SQLAlchemy engine setup; no tables are declared or created here."""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import database_url


class Base(DeclarativeBase):
    """Base reserved for future CRM models."""


engine = create_engine(database_url(), pool_pre_ping=True)

# This describes the existing table for SELECT/INSERT statements only. It is
# intentionally not registered as a migration model and is never created.
metadata = MetaData()
users_table = Table(
    "users",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("first_name", String),
    Column("last_name", String),
    Column("email", String),
    Column("phone", String),
    Column("password", Text),
    Column("user_type_id", Integer),
    Column("status", Integer),
    Column("created_at"),
    Column("updated_at"),
    Column("created_by", Integer),
    Column("updated_by", Integer),
)
lead_assignments_table = Table(
    "lead_assignments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("lead_id", Integer),
    Column("user_id", Integer, ForeignKey("users.user_id")),
    Column("assigned_type_id", Integer),
    Column("assigned_at"),
    Column("unassigned_at"),
    Column("comments", Text),
)
user_types_table = Table(
    "user_types",
    metadata,
    Column("user_type_id", Integer, primary_key=True),
    Column("name", String),
)
market_sources_table = Table(
    "market_sources",
    metadata,
    Column("market_source_id", Integer, primary_key=True),
    Column("name", String),
)
priority_table = Table(
    "priority",
    metadata,
    Column("priority_id", Integer, primary_key=True),
    Column("name", String),
)
market_types_table = Table(
    "market_types",
    metadata,
    Column("market_type_id", Integer, primary_key=True),
    Column("name", String),
)
leads_table = Table(
    "leads",
    metadata,
    Column("lead_id", Integer, primary_key=True),
    Column("company", String),
    Column("name", String),
    Column("email", String),
    Column("phone", String),
    Column("source", String),
    Column("message", Text),
    Column("campaign_id", String),
    Column("location", String),
    Column("priority_id", Integer, ForeignKey("priority.priority_id")),
    Column("market_source_id", Integer, ForeignKey(
        "market_sources.market_source_id")),
    Column("meta_leadgen_id", String, unique=True),
    Column("created_at"),
    Column("updated_at"),
)
