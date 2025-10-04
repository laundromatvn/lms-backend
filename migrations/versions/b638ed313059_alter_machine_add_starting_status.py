"""alter_machine_add_starting_status

Revision ID: b638ed313059
Revises: c78c252e2e0f
Create Date: 2025-10-04 22:19:01.309479

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b638ed313059'
down_revision = 'c78c252e2e0f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add starting status to machine_status enum
    op.execute("ALTER TYPE machine_status ADD VALUE 'STARTING'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For now, we'll leave the STARTING value in place
    pass
