"""add_payment_method_details_to_payments

Revision ID: 5f908d78f3c2
Revises: 4bb0821f7ac1
Create Date: 2025-10-05 16:29:16.763478

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f908d78f3c2'
down_revision = '4bb0821f7ac1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add payment_method_details column to payments table
    op.add_column('payments', 
        sa.Column('payment_method_details', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # Drop payment_method_details column from payments table
    op.drop_column('payments', 'payment_method_details')
