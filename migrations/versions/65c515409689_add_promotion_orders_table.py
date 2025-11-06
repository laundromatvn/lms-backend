"""add_promotion_order_table

Revision ID: 65c515409689
Revises: 37c6404dc45c
Create Date: 2025-11-04 17:41:16.549697

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '65c515409689'
down_revision = '37c6404dc45c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promotion_orders table
    op.create_table(
        'promotion_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
    )
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_promotion_orders_promotion_id',
        'promotion_orders',
        'promotion_campaigns',
        ['promotion_id'],
        ['id']
    )
    
    op.create_foreign_key(
        'fk_promotion_orders_order_id',
        'promotion_orders',
        'orders',
        ['order_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_promotion_orders_order_id', 'promotion_orders', type_='foreignkey')
    op.drop_constraint('fk_promotion_orders_promotion_id', 'promotion_orders', type_='foreignkey')
    
    # Drop promotion_orders table
    op.drop_table('promotion_orders')
