"""add_machine_table_and_update_controller

Revision ID: 789012345abc
Revises: 456789012def
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '789012345abc'
down_revision = '456789012def'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create machine_type enum type
    machine_type_enum = postgresql.ENUM(
        'WASHER', 'DRYER',
        name='machine_type',
        create_type=False
    )
    machine_type_enum.create(op.get_bind())
    
    # Create machine_status enum type
    machine_status_enum = postgresql.ENUM(
        'PENDING_SETUP', 'IDLE', 'BUSY', 'OUT_OF_SERVICE',
        name='machine_status',
        create_type=False
    )
    machine_status_enum.create(op.get_bind())
    
    # Add total_relays column to controllers table
    op.add_column('controllers', sa.Column('total_relays', sa.Integer(), nullable=False, server_default='0'))
    
    # Create machines table
    op.create_table(
        'machines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('controller_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('relay_no', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('machine_type', machine_type_enum, nullable=False, index=True),
        sa.Column('details', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('base_price', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('status', machine_status_enum, nullable=False, server_default='PENDING_SETUP', index=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_machines_controller_id', 'machines', 'controllers', ['controller_id'], ['id'])
    
    # Create unique constraint for controller_id + relay_no combination
    op.create_unique_constraint('uq_machines_controller_relay', 'machines', ['controller_id', 'relay_no'])


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_machines_controller_relay', 'machines', type_='unique')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_machines_controller_id', 'machines', type_='foreignkey')
    
    # Drop machines table
    op.drop_table('machines')
    
    # Remove total_relays column from controllers table
    op.drop_column('controllers', 'total_relays')
    
    # Drop enum types
    machine_status_enum = postgresql.ENUM(
        'PENDING_SETUP', 'IDLE', 'BUSY', 'OUT_OF_SERVICE',
        name='machine_status',
        create_type=False
    )
    machine_status_enum.drop(op.get_bind())
    
    machine_type_enum = postgresql.ENUM(
        'WASHER', 'DRYER',
        name='machine_type',
        create_type=False
    )
    machine_type_enum.drop(op.get_bind())
