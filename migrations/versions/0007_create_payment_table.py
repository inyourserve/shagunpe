# migrations/versions/0007_create_payments_table.py
"""create payments table

Revision ID: 0007
Revises: 0006
Create Date: 2024-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB

# revision identifiers
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for payment status
    # try:
    #     op.execute("CREATE TYPE payment_status AS ENUM ('initiated', 'processing', 'completed', 'failed')")
    # except Exception as e:
    #     if 'already exists' not in str(e):
    #         raise e

    # Create payments table
    op.create_table(
        "payments",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "transaction_id",
            UUID(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column(
            "payment_method", sa.String(20), nullable=False
        ),  # upi, card, net_banking
        sa.Column(
            "status",
            ENUM(
                "initiated", "processing", "completed", "failed", name="payment_status"
            ),
            nullable=False,
            server_default="initiated",
        ),
        sa.Column("gateway_payment_id", sa.String(100)),
        sa.Column("gateway_response", JSONB),
        sa.Column("metadata", JSONB),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_payments_transaction", "payments", ["transaction_id"])
    op.create_index("idx_payments_status", "payments", ["status"])
    op.create_index(
        "idx_payments_gateway_id", "payments", ["gateway_payment_id"], unique=True
    )
    op.create_index("idx_payments_created", "payments", ["created_at"])


def downgrade() -> None:
    op.drop_table("payments")
    op.execute("DROP TYPE IF EXISTS payment_status")
