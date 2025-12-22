"""alter_user_table_drop_unique_email_and_phone_constraint

Revision ID: 4c4745368099
Revises: 2cb2efb23b8c
Create Date: 2025-12-21 22:38:17.739196

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4c4745368099'
down_revision = '2cb2efb23b8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_users_phone', 'users')
    op.drop_index('ix_users_email', 'users')
    
    op.create_unique_constraint('uq_user_phone_email', 'users', ['phone', 'email'])

def downgrade() -> None:
    op.drop_index('uq_user_phone_email', 'users')
    
    op.create_unique_constraint('ix_users_phone', 'users', ['phone'])
    op.create_unique_constraint('ix_users_email', 'users', ['email'])
