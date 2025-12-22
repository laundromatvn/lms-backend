"""add_permissions_table

Revision ID: 8be8886b44c6
Revises: c2db48ece4bb
Create Date: 2025-11-22 01:46:12.188102

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8be8886b44c6'
down_revision = 'c2db48ece4bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    op.create_index(op.f('ix_permissions_is_enabled'), 'permissions', ['is_enabled'], unique=False)

def downgrade() -> None:
    op.drop_table('permissions')
