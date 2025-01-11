# migrations/versions/0006_create_optimized_transactions.py
"""create optimized transactions table

Revision ID: 0006
Revises: 0005
Create Date: 2024-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB

# revision identifiers
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    # Drop existing types using raw SQL to check if they exist first

    # Now create the types
    # op.execute("CREATE TYPE transaction_type AS ENUM ('online', 'cash')")
    # op.execute("CREATE TYPE transaction_status AS ENUM ('pending', 'completed', 'failed')")

    # Create transactions table
    op.create_table(
        "transactions",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "event_id",
            UUID(),
            sa.ForeignKey("events.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "receiver_id",
            UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
        sa.Column(
            "type", ENUM("online", "cash", name="transaction_type"), nullable=False
        ),
        sa.Column(
            "status",
            ENUM("pending", "completed", "failed", name="transaction_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("sender_name", sa.String(100)),
        sa.Column("address", sa.String(200)),
        sa.Column("message", sa.Text),
        sa.Column("location", JSONB),
        sa.Column("gift_details", JSONB),
        sa.Column("upi_ref", sa.String(100)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        "idx_transactions_event_type_created",
        "transactions",
        ["event_id", "type", "created_at"],
    )
    op.create_index(
        "idx_transactions_sender", "transactions", ["sender_id", "created_at"]
    )
    op.create_index(
        "idx_transactions_receiver", "transactions", ["receiver_id", "created_at"]
    )
    op.create_index(
        "idx_transactions_status_type",
        "transactions",
        ["status", "type"],
        postgresql_where=sa.text("type = 'online'"),
    )
    op.create_index(
        "idx_transactions_sender_name",
        "transactions",
        ["sender_name"],
        postgresql_where=sa.text("type = 'cash'"),
    )
    op.execute(
        "CREATE INDEX idx_transactions_location ON transactions USING GIN (location jsonb_path_ops)"
    )
    op.execute(
        "CREATE INDEX idx_transactions_gift_details ON transactions USING GIN (gift_details jsonb_path_ops)"
    )
    op.create_index(
        "idx_transactions_upi_ref",
        "transactions",
        ["upi_ref"],
        unique=True,
        postgresql_where=sa.text("upi_ref IS NOT NULL"),
    )


def downgrade() -> None:
    # Drop indexes first (though dropping table will drop its indexes automatically)
    op.drop_table("transactions")
