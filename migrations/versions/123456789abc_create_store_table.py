"""create_store_table

Revision ID: 123456789abc
Revises: 0406522cbb6e
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '0406522cbb6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create store_status enum type
    store_status_enum = postgresql.ENUM(
        'ACTIVE', 'INACTIVE',
        name='store_status',
        create_type=False
    )
    store_status_enum.create(op.get_bind())
    
    # Create stores table
    op.create_table(
        'stores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('status', store_status_enum, nullable=False, default='ACTIVE', index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('contact_phone_number', sa.String(20), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_stores_created_by', 'stores', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_stores_updated_by', 'stores', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_stores_deleted_by', 'stores', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_stores_tenant_id', 'stores', 'tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_stores_tenant_id', 'stores', type_='foreignkey')
    op.drop_constraint('fk_stores_deleted_by', 'stores', type_='foreignkey')
    op.drop_constraint('fk_stores_updated_by', 'stores', type_='foreignkey')
    op.drop_constraint('fk_stores_created_by', 'stores', type_='foreignkey')
    
    # Drop stores table
    op.drop_table('stores')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS store_status')
