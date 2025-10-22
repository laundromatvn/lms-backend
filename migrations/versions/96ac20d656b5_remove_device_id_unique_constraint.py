"""remove_device_id_unique_constraint

Revision ID: 96ac20d656b5
Revises: e0d38acd3ee3
Create Date: 2025-10-23 01:08:20.123988

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '96ac20d656b5'
down_revision = 'e0d38acd3ee3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('controllers_device_id_key', 'controllers', type_='unique') 


def downgrade() -> None:
    op.create_unique_constraint('controllers_device_id_key', 'controllers', ['device_id'])
