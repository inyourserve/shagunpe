# migrations/versions/xxxx_add_sender_details_to_transactions.py
"""add sender details to transactions

Revision ID: xxxx
Revises: xxxx
Create Date: 2024-01-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0005"
down_revision = "0004"  # Put your previous migration revision id here
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sender details columns to transactions table
    op.add_column("transactions", sa.Column("sender_name", sa.String(100)))
    op.add_column("transactions", sa.Column("sender_village", sa.String(100)))


def downgrade() -> None:
    # Remove the columns if needed to rollback
    op.drop_column("transactions", "sender_name")
    op.drop_column("transactions", "sender_village")
