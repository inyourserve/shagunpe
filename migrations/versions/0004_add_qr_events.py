# migrations/versions/xxxx_add_qr_code_to_events.py
"""add qr code to events

Revision ID: 0004
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("qr_code", sa.Text))
    op.add_column(
        "events", sa.Column("qr_code_updated_at", sa.TIMESTAMP(timezone=True))
    )


def downgrade() -> None:
    op.drop_column("events", "qr_code")
    op.drop_column("events", "qr_code_updated_at")
