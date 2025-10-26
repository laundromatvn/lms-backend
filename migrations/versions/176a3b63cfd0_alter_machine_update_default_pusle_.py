"""alter_machine_update_default_pusle_duration

Revision ID: 176a3b63cfd0
Revises: 96ac20d656b5
Create Date: 2025-10-26 23:40:23.533672

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "176a3b63cfd0"
down_revision = "96ac20d656b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing records to have pulse_duration = 50 if they currently have 1000
    op.execute("UPDATE machines SET pulse_duration = 50 WHERE pulse_duration = 1000")

    # Alter the column to set the new default value
    op.alter_column(
        "machines",
        "pulse_duration",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="50",
    )


def downgrade() -> None:
    # Revert existing records back to pulse_duration = 1000
    op.execute("UPDATE machines SET pulse_duration = 1000 WHERE pulse_duration = 50")

    # Alter the column to set the old default value
    op.alter_column(
        "machines",
        "pulse_duration",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="1000",
    )
