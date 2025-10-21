"""create_datapoints_table

Revision ID: e0d38acd3ee3
Revises: 23fda618ff55
Create Date: 2025-10-21 15:31:40.654768

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e0d38acd3ee3'
down_revision = '23fda618ff55'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create datapoint_value_type enum type
    datapoint_value_type_enum = postgresql.ENUM(
        'MACHINE_STATE',
        name='datapoint_value_type',
        create_type=False
    )
    datapoint_value_type_enum.create(op.get_bind())
    
    # Create datapoints table
    op.create_table('datapoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('controller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('relay_no', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('value_type', postgresql.ENUM('MACHINE_STATE', name='datapoint_value_type', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['controller_id'], ['controllers.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_datapoints_id'), 'datapoints', ['id'], unique=False)
    op.create_index(op.f('ix_datapoints_tenant_id'), 'datapoints', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_datapoints_store_id'), 'datapoints', ['store_id'], unique=False)
    op.create_index(op.f('ix_datapoints_controller_id'), 'datapoints', ['controller_id'], unique=False)
    op.create_index(op.f('ix_datapoints_machine_id'), 'datapoints', ['machine_id'], unique=False)
    op.create_index(op.f('ix_datapoints_relay_no'), 'datapoints', ['relay_no'], unique=False)
    op.create_index(op.f('ix_datapoints_value_type'), 'datapoints', ['value_type'], unique=False)
    
    # Create composite indexes for common queries
    op.create_index('ix_datapoints_controller_relay', 'datapoints', ['controller_id', 'relay_no'], unique=False)
    op.create_index('ix_datapoints_controller_value_type', 'datapoints', ['controller_id', 'value_type'], unique=False)
    op.create_index('ix_datapoints_created_at_controller', 'datapoints', ['created_at', 'controller_id'], unique=False)
    op.create_index('ix_datapoints_machine_relay', 'datapoints', ['machine_id', 'relay_no'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_datapoints_machine_relay', table_name='datapoints')
    op.drop_index('ix_datapoints_created_at_controller', table_name='datapoints')
    op.drop_index('ix_datapoints_controller_value_type', table_name='datapoints')
    op.drop_index('ix_datapoints_controller_relay', table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_value_type'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_relay_no'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_machine_id'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_controller_id'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_store_id'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_tenant_id'), table_name='datapoints')
    op.drop_index(op.f('ix_datapoints_id'), table_name='datapoints')
    
    # Drop table
    op.drop_table('datapoints')
    
    # Drop enum type
    op.execute('DROP TYPE datapoint_value_type')
