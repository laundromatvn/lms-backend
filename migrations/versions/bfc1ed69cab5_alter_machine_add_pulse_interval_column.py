"""alter_machine_add_pulse_interval_column

Revision ID: bfc1ed69cab5
Revises: 176a3b63cfd0
Create Date: 2025-10-28 14:12:56.591241

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bfc1ed69cab5'
down_revision = '176a3b63cfd0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('machines', sa.Column('pulse_interval', sa.Integer(), nullable=True))
    op.execute("UPDATE machines SET pulse_interval = 100 WHERE pulse_interval IS NULL")
    op.alter_column('machines', 'pulse_interval', nullable=False)
    op.alter_column('machines', 'pulse_interval', server_default='100')

def downgrade() -> None:
    op.drop_column('machines', 'pulse_interval')
