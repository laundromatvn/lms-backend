"""add_notifications_table

Revision ID: 2cb2efb23b8c
Revises: 9ce8baa04bea
Create Date: 2025-12-19 01:10:37.620267

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2cb2efb23b8c'
down_revision = '9ce8baa04bea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_type enum type
    notification_type_enum = postgresql.ENUM(
        'INFO', 'ERROR',
        name='notification_type',
        create_type=False
    )
    notification_type_enum.create(op.get_bind())
    
    # Create notification_status enum type
    notification_status_enum = postgresql.ENUM(
        'NEW', 'DELIVERED', 'SEEN', 'FAILED',
        name='notification_status',
        create_type=False
    )
    notification_status_enum.create(op.get_bind())
    
    # Create notification_channel enum type
    notification_channel_enum = postgresql.ENUM(
        'IN_APP',
        name='notification_channel',
        create_type=False
    )
    notification_channel_enum.create(op.get_bind())
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('type', notification_type_enum, nullable=False, default='INFO', index=True),
        sa.Column('status', notification_status_enum, nullable=False, default='NEW', index=True),
        sa.Column('channel', notification_channel_enum, nullable=False, default='IN_APP', index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
    )

    # Add foreign key constraints
    op.create_foreign_key('fk_notifications_user_id', 'notifications', 'users', ['user_id'], ['id'])

def downgrade() -> None:
    op.drop_table('notifications')
