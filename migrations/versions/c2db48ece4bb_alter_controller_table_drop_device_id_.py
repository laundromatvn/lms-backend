"""alter_controller_table_drop_device_id_unique_constraint

Revision ID: c2db48ece4bb
Revises: 3cb48e2150a0
Create Date: 2025-11-25 22:54:50.255455

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'c2db48ece4bb'
down_revision = '3cb48e2150a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_controllers_device_id', table_name='controllers')


def downgrade() -> None:
    op.create_index(
        'ix_controllers_device_id',
        'controllers',
        ['device_id'],
        unique=True,
    )
