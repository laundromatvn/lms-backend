"""alter_order_table_add_promotion_columns

Revision ID: 37c6404dc45c
Revises: 952f199511f3
Create Date: 2025-11-04 17:40:57.139032

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '37c6404dc45c'
down_revision = '952f199511f3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sub_total column
    op.add_column('orders', 
        sa.Column('sub_total', sa.Numeric(10, 2), nullable=False, server_default='0.00')
    )
    
    # Add discount_amount column
    op.add_column('orders',
        sa.Column('discount_amount', sa.Numeric(10, 2), nullable=False, server_default='0.00')
    )
    
    # Add promotion_summary column (JSON)
    op.add_column('orders',
        sa.Column('promotion_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}')
    )


def downgrade() -> None:
    # Drop promotion_summary column
    op.drop_column('orders', 'promotion_summary')
    
    # Drop discount_amount column
    op.drop_column('orders', 'discount_amount')
    
    # Drop sub_total column
    op.drop_column('orders', 'sub_total')
