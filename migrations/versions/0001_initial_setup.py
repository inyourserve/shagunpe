"""initial setup

Revision ID: 0001
Revises:
Create Date: 2024-01-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("phone", sa.String(15), nullable=False),
        sa.Column("name", sa.String(100)),
        sa.Column("village", sa.String(100)),
        sa.Column("profile_photo_url", sa.String(255)),
        sa.Column("preferred_language", sa.String(10), server_default="en"),
        sa.Column("status", sa.String(10), server_default="active"),
        sa.Column("device_token", sa.Text),
        sa.Column("device_info", JSONB),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_users_phone", "users", ["phone"], unique=True)
    op.create_index("idx_users_status", "users", ["status"])

    # Wallets table
    op.create_table(
        "wallets",
        sa.Column(
            "id", UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", UUID(), nullable=False),
        sa.Column("balance", sa.Numeric(20, 2), server_default="0", nullable=False),
        sa.Column(
            "hold_balance", sa.Numeric(20, 2), server_default="0", nullable=False
        ),
        sa.Column(
            "last_updated", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()")
        ),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("balance >= 0", name="positive_balance"),
    )

    op.create_index("idx_wallets_user_id", "wallets", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_table("wallets")
    op.drop_table("users")
