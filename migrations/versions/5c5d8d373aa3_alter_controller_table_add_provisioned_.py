"""alter_controller_table_add_provisioned_firmware_id_column

Revision ID: 5c5d8d373aa3
Revises: cf12a3f0158b
Create Date: 2025-11-11 17:22:34.461354

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5c5d8d373aa3'
down_revision = 'cf12a3f0158b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('controllers', sa.Column('provisioned_firmware_id', postgresql.UUID(as_uuid=True), nullable=True, index=True))
    op.create_foreign_key('fk_controllers_provisioned_firmware_id', 'controllers', 'firmwares', ['provisioned_firmware_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_controllers_provisioned_firmware_id', 'controllers', type_='foreignkey')
    op.drop_column('controllers', 'provisioned_firmware_id')
