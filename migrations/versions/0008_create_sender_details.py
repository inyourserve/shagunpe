# migrations/versions/xxxx_create_sender_details.py
"""create sender details table

Revision ID: xxxx
Revises: xxxx
Create Date: 2024-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sender_details",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "user_id",
            UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.String(200), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_sender_details_user", "sender_details", ["user_id"])
    op.create_index("idx_sender_details_name", "sender_details", ["name"])


def downgrade() -> None:
    op.drop_table("sender_details")
