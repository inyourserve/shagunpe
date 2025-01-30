# alembic/versions/XXXXXXXXXXXX_add_trigram_search_indexes.py
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    # Create extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_sender_name_trigram 
        ON transactions USING gin (sender_name gin_trgm_ops)
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_transactions_address_trigram 
        ON transactions USING gin (address gin_trgm_ops)
    """
    )


def downgrade():
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_transactions_sender_name_trigram")
    op.execute("DROP INDEX IF EXISTS idx_transactions_address_trigram")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pg_trgm CASCADE")
