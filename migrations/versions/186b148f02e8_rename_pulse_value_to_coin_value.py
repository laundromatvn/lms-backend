"""rename_pulse_value_to_coin_value

Revision ID: 186b148f02e8
Revises: f1a2b3c4d5e6
Create Date: 2025-10-06 18:28:21.170984

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '186b148f02e8'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename pulse_value column to coin_value in machines table
    op.alter_column('machines', 'pulse_value', new_column_name='coin_value')


def downgrade() -> None:
    # Rename coin_value column back to pulse_value in machines table
    op.alter_column('machines', 'coin_value', new_column_name='pulse_value')
