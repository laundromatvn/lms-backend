"""create_controller_table

Revision ID: 456789012def
Revises: 123456789abc
Create Date: 2025-01-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '456789012def'
down_revision = '123456789abc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create controller_status enum type
    controller_status_enum = postgresql.ENUM(
        'NEW', 'ACTIVE', 'INACTIVE',
        name='controller_status',
        create_type=False
    )
    controller_status_enum.create(op.get_bind())
    
    # Create controllers table
    op.create_table(
        'controllers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', controller_status_enum, nullable=False, default='NEW', index=True),
        sa.Column('device_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=True, index=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_controllers_store_id', 'controllers', 'stores', ['store_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_controllers_store_id', 'controllers', type_='foreignkey')
    
    # Drop controllers table
    op.drop_table('controllers')
    
    # Drop controller_status enum type
    controller_status_enum = postgresql.ENUM(
        'NEW', 'ACTIVE', 'INACTIVE',
        name='controller_status',
        create_type=False
    )
    controller_status_enum.drop(op.get_bind())
