"""create_tenant_table

Revision ID: 0406522cbb6e
Revises: 372533266ebe
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0406522cbb6e'
down_revision = '372533266ebe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenant_status enum type
    tenant_status_enum = postgresql.ENUM(
        'ACTIVE', 'INACTIVE',
        name='tenant_status',
        create_type=False
    )
    tenant_status_enum.create(op.get_bind())
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('status', tenant_status_enum, nullable=False, default='ACTIVE', index=True),
        sa.Column('contact_email', sa.String(255), nullable=False, index=True),
        sa.Column('contact_phone_number', sa.String(20), nullable=False, index=True),
        sa.Column('contact_full_name', sa.String(255), nullable=False),
        sa.Column('contact_address', sa.String(500), nullable=False),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_tenants_created_by', 'tenants', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_tenants_updated_by', 'tenants', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_tenants_deleted_by', 'tenants', 'users', ['deleted_by'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_tenants_deleted_by', 'tenants', type_='foreignkey')
    op.drop_constraint('fk_tenants_updated_by', 'tenants', type_='foreignkey')
    op.drop_constraint('fk_tenants_created_by', 'tenants', type_='foreignkey')
    
    # Drop tenants table
    op.drop_table('tenants')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS tenant_status')
