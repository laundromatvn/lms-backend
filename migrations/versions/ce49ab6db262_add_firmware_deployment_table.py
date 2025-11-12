"""add_firmware_deployment_table

Revision ID: ce49ab6db262
Revises: 5c5d8d373aa3
Create Date: 2025-11-11 21:03:41.083208

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ce49ab6db262'
down_revision = '5c5d8d373aa3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create firmware_deployment_status enum type
    firmware_deployment_status_enum = postgresql.ENUM(
        'NEW', 'REBOOTING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='firmware_deployment_status',
        create_type=False
    )
    firmware_deployment_status_enum.create(op.get_bind())
    
    # Create firmware_deployments table
    op.create_table(
        'firmware_deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('firmware_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('controller_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('status', firmware_deployment_status_enum, nullable=False, default='NEW', server_default='NEW', index=True),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_firmware_deployments_firmware_id', 'firmware_deployments', 'firmwares', ['firmware_id'], ['id'])
    op.create_foreign_key('fk_firmware_deployments_controller_id', 'firmware_deployments', 'controllers', ['controller_id'], ['id'])

    # Ensure unique combination of firmware_id and controller_id
    op.create_unique_constraint('uix_firmware_id_controller_id', 'firmware_deployments', ['firmware_id', 'controller_id'])

def downgrade() -> None:
    op.drop_table('firmware_deployments')

    # Drop firmware_deployment_status enum type
    firmware_deployment_status_enum = postgresql.ENUM(
        'NEW', 'REBOOTING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='firmware_deployment_status',
        create_type=False
    )
    firmware_deployment_status_enum.drop(op.get_bind())
