"""alter_machine_table_drop_name_unique_constraint

Revision ID: 43e90c7dd0bb
Revises: 8be8886b44c6
Create Date: 2025-12-16 10:50:11.613368

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '43e90c7dd0bb'
down_revision = '8be8886b44c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_machines_name', 'machines')


def downgrade() -> None:
    op.create_index('ix_machines_name', table_name='machines', column_names=['name'], unique=True)
