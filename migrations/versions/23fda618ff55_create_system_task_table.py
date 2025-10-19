"""create_system_task_table

Revision ID: 23fda618ff55
Revises: 186b148f02e8
Create Date: 2025-10-19 19:29:31.892797

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '23fda618ff55'
down_revision = '186b148f02e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create system_task_status enum type
    system_task_status_enum = postgresql.ENUM(
        'NEW', 'IN_PROGRESS', 'SUCCESS', 'FAILED',
        name='system_task_status',
        create_type=False
    )
    system_task_status_enum.create(op.get_bind())
    
    # Create system_tasks table
    op.create_table('system_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_time', sa.Integer(), nullable=True),
        sa.Column('task_type', sa.String(length=100), nullable=True),
        sa.Column('status', postgresql.ENUM('NEW', 'IN_PROGRESS', 'SUCCESS', 'FAILED', name='system_task_status', create_type=False), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_system_tasks_id'), 'system_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_system_tasks_expired_at'), 'system_tasks', ['expired_at'], unique=False)
    op.create_index(op.f('ix_system_tasks_status'), 'system_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_system_tasks_task_type'), 'system_tasks', ['task_type'], unique=False)
    
    # Create composite index for common queries
    op.create_index('ix_system_tasks_status_task_type', 'system_tasks', ['status', 'task_type'], unique=False)
    op.create_index('ix_system_tasks_expired_at_status', 'system_tasks', ['expired_at', 'status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_system_tasks_expired_at_status', table_name='system_tasks')
    op.drop_index('ix_system_tasks_status_task_type', table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_task_type'), table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_status'), table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_expired_at'), table_name='system_tasks')
    op.drop_index(op.f('ix_system_tasks_id'), table_name='system_tasks')
    
    # Drop table
    op.drop_table('system_tasks')
    
    # Drop enum type
    op.execute('DROP TYPE system_task_status')
