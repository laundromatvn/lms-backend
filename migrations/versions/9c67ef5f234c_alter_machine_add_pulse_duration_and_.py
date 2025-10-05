"""alter_machine_add_pulse_duration_and_add_ons_settings

Revision ID: 9c67ef5f234c
Revises: b638ed313059
Create Date: 2025-10-05 09:43:56.772180

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9c67ef5f234c'
down_revision = 'b638ed313059'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pulse_duration and add_ons_options columns to machines table
    # First add columns as nullable
    op.add_column('machines', sa.Column('pulse_duration', sa.Integer(), nullable=True))
    op.add_column('machines', sa.Column('pulse_value', sa.Integer(), nullable=True))
    op.add_column('machines', sa.Column('add_ons_options', postgresql.JSONB(), nullable=True))
    
    # Update existing rows with default values
    op.execute("UPDATE machines SET pulse_duration = 1000 WHERE pulse_duration IS NULL")
    op.execute("UPDATE machines SET pulse_value = 10 WHERE pulse_value IS NULL")
    op.execute("UPDATE machines SET add_ons_options = '[]'::jsonb WHERE add_ons_options IS NULL")
    
    # Now make columns NOT NULL
    op.alter_column('machines', 'pulse_duration', nullable=False)
    op.alter_column('machines', 'pulse_value', nullable=False)


def downgrade() -> None:
    # Drop pulse_duration and add_ons_options columns from machines table
    op.drop_column('machines', 'pulse_duration')
    op.drop_column('machines', 'pulse_value')
    op.drop_column('machines', 'add_ons_options')
