"""alter_payment_table_add_vnpay_payment_provider

Revision ID: 3cb48e2150a0
Revises: ce49ab6db262
Create Date: 2025-11-13 18:46:34.464031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cb48e2150a0'
down_revision = 'ce49ab6db262'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE payment_provider ADD VALUE 'VNPAY'")


def downgrade() -> None:
    pass
