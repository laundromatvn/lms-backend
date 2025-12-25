"""add_permission_group_permissions_table

Revision ID: cdc9fba324ee
Revises: f3e6fe0c2f78
Create Date: 2025-12-26 00:39:53.307351

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'cdc9fba324ee'
down_revision = 'f3e6fe0c2f78'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permission_group_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('permission_group_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('permission_id', sa.Integer(), nullable=False, index=True),
    )
    
    op.create_foreign_key('fk_permission_group_permissions_permission_group_id', 'permission_group_permissions', 'permission_groups', ['permission_group_id'], ['id'])
    op.create_foreign_key('fk_permission_group_permissions_permission_id', 'permission_group_permissions', 'permissions', ['permission_id'], ['id'])
    op.create_unique_constraint('uq_permission_group_permission_group_permission', 'permission_group_permissions', ['permission_group_id', 'permission_id'])


def downgrade() -> None:
    op.drop_table('permission_group_permissions')
