"""add_internal_promotion_and_discount_full_to_payment_enums

Revision ID: fd296a74492a
Revises: 65c515409689
Create Date: 2025-11-05 00:19:48.578438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd296a74492a'
down_revision = '65c515409689'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE payment_provider ADD VALUE 'INTERNAL_PROMOTION'")
    op.execute("ALTER TYPE payment_method ADD VALUE 'DISCOUNT_FULL'")


def downgrade() -> None:
    op.execute("ALTER TYPE payment_provider DROP VALUE 'INTERNAL_PROMOTION'")
    op.execute("ALTER TYPE payment_method DROP VALUE 'DISCOUNT_FULL'")
