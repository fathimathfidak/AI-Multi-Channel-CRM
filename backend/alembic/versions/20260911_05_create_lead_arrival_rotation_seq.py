"""Create the dedicated PostgreSQL lead arrival rotation sequence."""

from alembic import op


revision = "20260911_05"
down_revision = "20260907_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS public.lead_arrival_rotation_seq
        AS BIGINT
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1
        """
    )


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS public.lead_arrival_rotation_seq")
