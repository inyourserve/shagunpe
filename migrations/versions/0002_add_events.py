# migrations/versions/0002_add_events.py
"""add events tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Events table
    op.create_table(
        "events",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("creator_id", UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("event_name", sa.String(200), nullable=False),
        sa.Column("guardian_name", sa.String(100)),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("village", sa.String(100)),
        sa.Column("location", sa.String(200)),
        sa.Column("shagun_id", sa.String(20), unique=True),  # For QR/sharing
        sa.Column("total_amount", sa.Numeric(20, 2), server_default="0"),
        sa.Column("online_amount", sa.Numeric(20, 2), server_default="0"),
        sa.Column("cash_amount", sa.Numeric(20, 2), server_default="0"),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_events_creator", "events", ["creator_id"])
    op.create_index("idx_events_date", "events", ["event_date"])
    op.create_index("idx_events_shagun_id", "events", ["shagun_id"], unique=True)
