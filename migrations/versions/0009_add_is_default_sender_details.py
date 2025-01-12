# migrations/versions/0009_add_is_default_to_sender_details.py
"""add is_default to sender details

Revision ID: 0009
Revises: 0008
Create Date: 2024-01-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_default column
    op.add_column(
        "sender_details",
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
    )

    # Create index for is_default
    op.create_index(
        "idx_sender_details_default", "sender_details", ["user_id", "is_default"]
    )

    # Set first sender detail for each user as default
    op.execute(
        """
        WITH ranked_details AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at ASC) as rn
            FROM sender_details
        )
        UPDATE sender_details
        SET is_default = true
        WHERE id IN (
            SELECT id 
            FROM ranked_details 
            WHERE rn = 1
        )
    """
    )


def downgrade() -> None:
    op.drop_index("idx_sender_details_default")
    op.drop_column("sender_details", "is_default")
