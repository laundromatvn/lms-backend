"""create_tenant_member_table

Revision ID: 3fe83f1b3c6e
Revises: abcdef123456
Create Date: 2025-09-28 14:40:11.313926

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3fe83f1b3c6e'
down_revision = '789012345abc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenant_members table
    op.create_table(
        'tenant_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, index=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_tenant_members_tenant_id', 'tenant_members', 'tenants', ['tenant_id'], ['id'])
    op.create_foreign_key('fk_tenant_members_user_id', 'tenant_members', 'users', ['user_id'], ['id'])
    
    # Create unique constraint for tenant_id + user_id combination
    op.create_unique_constraint('uq_tenant_member_tenant_user', 'tenant_members', ['tenant_id', 'user_id'])


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_tenant_member_tenant_user', 'tenant_members', type_='unique')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_tenant_members_user_id', 'tenant_members', type_='foreignkey')
    op.drop_constraint('fk_tenant_members_tenant_id', 'tenant_members', type_='foreignkey')
    
    # Drop tenant_members table
    op.drop_table('tenant_members')
