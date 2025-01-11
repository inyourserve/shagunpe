# migrations/versions/0003_add_transactions.py
"""add transactions table

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Transactions table
    op.create_table(
        "transactions",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("event_id", UUID(), sa.ForeignKey("events.id", ondelete="SET NULL")),
        sa.Column("sender_id", UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column(
            "receiver_id", UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),  # 'online' or 'cash'
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("upi_ref", sa.String(100)),  # For online transactions
        sa.Column("location", JSONB),  # Store sender's location
        sa.Column("gift_details", JSONB),  # Optional gift details
        sa.Column("message", sa.Text),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_transactions_event", "transactions", ["event_id"])
    op.create_index("idx_transactions_sender", "transactions", ["sender_id"])
    op.create_index("idx_transactions_receiver", "transactions", ["receiver_id"])
    op.create_index("idx_transactions_created_at", "transactions", ["created_at"])
    op.create_index("idx_transactions_status", "transactions", ["status"])


def downgrade() -> None:
    op.drop_table("transactions")
