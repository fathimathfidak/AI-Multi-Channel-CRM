"""Add normalized market source relationship to leads."""

from alembic import op
import sqlalchemy as sa


revision = "20260905_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("market_source_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_leads_market_source_id_market_sources",
        "leads",
        "market_sources",
        ["market_source_id"],
        ["market_source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_leads_market_source_id_market_sources",
        "leads",
        type_="foreignkey",
    )
    op.drop_column("leads", "market_source_id")
