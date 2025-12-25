"""add_permission_groups_table

Revision ID: f3e6fe0c2f78
Revises: 4c4745368099
Create Date: 2025-12-25 19:21:23.545702

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f3e6fe0c2f78'
down_revision = '4c4745368099'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permission_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
    )

    op.create_foreign_key('fk_permission_groups_created_by', 'permission_groups', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_permission_groups_updated_by', 'permission_groups', 'users', ['updated_by'], ['id'])

def downgrade() -> None:
    op.drop_table('permission_groups')
