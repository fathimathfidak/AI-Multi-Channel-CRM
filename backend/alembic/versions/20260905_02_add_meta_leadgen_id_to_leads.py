"""Add the external Meta lead identifier to CRM leads."""

from alembic import op
import sqlalchemy as sa


revision = "20260905_02"
down_revision = "20260905_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("meta_leadgen_id", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_leads_meta_leadgen_id",
        "leads",
        ["meta_leadgen_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_leads_meta_leadgen_id",
        "leads",
        type_="unique",
    )
    op.drop_column("leads", "meta_leadgen_id")
