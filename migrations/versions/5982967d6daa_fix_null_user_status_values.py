"""fix_null_user_status_values

Revision ID: 5982967d6daa
Revises: eadd04e62bf3
Create Date: 2025-09-22 11:39:43.452186

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5982967d6daa'
down_revision = 'eadd04e62bf3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update any users with NULL status to have 'NEW' status
    op.execute("UPDATE users SET status = 'NEW' WHERE status IS NULL")


def downgrade() -> None:
    # This migration only fixes data, no schema changes to revert
    pass
