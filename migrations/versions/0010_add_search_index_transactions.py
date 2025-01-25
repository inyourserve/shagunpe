# migrations/versions/0010_add_search_indexes.py
"""add search indexes

Revision ID: 0010
Revises: 0009
Create Date: 2024-01-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First create the extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create indexes for faster searching
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_sender_name_trgm 
        ON transactions 
        USING gin (sender_name gin_trgm_ops)
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_address_trgm 
        ON transactions 
        USING gin (address gin_trgm_ops)
    """
    )

    # Create index for type and status
    op.create_index("idx_transactions_type_status", "transactions", ["type", "status"])

    # Create index for event_id and created_at (correct syntax)
    op.execute(
        """
        CREATE INDEX idx_transactions_event_created 
        ON transactions (event_id, created_at DESC)
    """
    )


def downgrade() -> None:
    # Drop all created indexes
    op.execute("DROP INDEX IF EXISTS idx_transactions_sender_name_trgm")
    op.execute("DROP INDEX IF EXISTS idx_transactions_address_trgm")
    op.drop_index("idx_transactions_type_status")
    op.drop_index("idx_transactions_event_created")
