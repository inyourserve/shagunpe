# migrations/versions/001_initial.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade():
    # Users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("phone", sa.String(15), unique=True, nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True)),
    )

    # OTP table
    op.create_table(
        "otp_requests",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("phone", sa.String(15), nullable=False),
        sa.Column("otp", sa.String(6), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("verified", sa.Boolean, default=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")
        ),
    )


def downgrade():
    op.drop_table("otp_requests")
    op.drop_table("users")
