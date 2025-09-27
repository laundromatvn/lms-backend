"""create_user_table

Revision ID: 372533266ebe
Revises: 
Create Date: 2025-09-27 15:18:55.180768

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '372533266ebe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    user_roles_enum = postgresql.ENUM(
        'ADMIN', 'TENANT_ADMIN', 'TENANT_STAFF', 'CUSTOMER',
        name='user_roles',
        create_type=False
    )
    user_roles_enum.create(op.get_bind())
    
    user_status_enum = postgresql.ENUM(
        'NEW', 'ACTIVE', 'INACTIVE', 'WAITING_FOR_APPROVAL',
        name='userstatus',
        create_type=False
    )
    user_status_enum.create(op.get_bind())
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('role', user_roles_enum, nullable=False, index=True),
        sa.Column('status', user_status_enum, nullable=False, default='NEW', index=True),
        sa.Column('phone', sa.String(20), unique=True, nullable=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('is_verified', sa.Boolean, nullable=False, default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Drop users table
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS userstatus')
    op.execute('DROP TYPE IF EXISTS user_roles')
