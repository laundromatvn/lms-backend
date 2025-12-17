"""add_store_members_table

Revision ID: 9ce8baa04bea
Revises: 43e90c7dd0bb
Create Date: 2025-12-18 01:17:49.181418

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9ce8baa04bea'
down_revision = '43e90c7dd0bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'store_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=sa.func.now()),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
    )

    op.create_foreign_key('fk_store_members_store_id', 'store_members', 'stores', ['store_id'], ['id'])
    op.create_foreign_key('fk_store_members_user_id', 'store_members', 'users', ['user_id'], ['id'])
    
    op.create_unique_constraint('uq_store_member_store_user', 'store_members', ['store_id', 'user_id'])


def downgrade() -> None:
    op.drop_table('store_members')
