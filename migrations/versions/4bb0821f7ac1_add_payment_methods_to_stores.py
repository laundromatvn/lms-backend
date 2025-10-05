"""add_payment_methods_to_stores

Revision ID: 4bb0821f7ac1
Revises: 9c67ef5f234c
Create Date: 2025-10-05 14:15:16.091149

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4bb0821f7ac1'
down_revision = '9c67ef5f234c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add payment_methods column to stores table
    op.add_column('stores', 
        sa.Column('payment_methods', 
            postgresql.JSON(astext_type=sa.Text()), 
            nullable=True, 
            server_default='[]'
        )
    )


def downgrade() -> None:
    # Drop payment_methods column from stores table
    op.drop_column('stores', 'payment_methods')
