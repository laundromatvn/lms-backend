"""alter_promotion_campaign_table_add_finish_status

Revision ID: 2ce4a8a035b0
Revises: fd296a74492a
Create Date: 2025-11-06 21:10:36.200952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ce4a8a035b0'
down_revision = 'fd296a74492a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add FINISHED status to promotion_campaign_status enum
    op.execute("ALTER TYPE promotion_campaign_status ADD VALUE 'FINISHED'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For now, we'll leave the FINISHED value in place
    pass
