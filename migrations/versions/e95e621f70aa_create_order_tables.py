"""create_order_tables

Revision ID: e95e621f70aa
Revises: 3fe83f1b3c6e
Create Date: 2025-09-30 18:19:38.758860

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e95e621f70aa'
down_revision = '3fe83f1b3c6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create order_status enum type
    order_status_enum = postgresql.ENUM(
        'NEW', 'CANCELLED', 'WAITING_FOR_PAYMENT', 'PAYMENT_FAILED', 
        'PAYMENT_SUCCESS', 'IN_PROGRESS', 'FINISHED',
        name='order_status',
        create_type=False
    )
    order_status_enum.create(op.get_bind())
    
    # Create order_detail_status enum type
    order_detail_status_enum = postgresql.ENUM(
        'NEW', 'IN_PROGRESS', 'FINISHED', 'CANCELLED',
        name='order_detail_status',
        create_type=False
    )
    order_detail_status_enum.create(op.get_bind())
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('status', order_status_enum, nullable=False, default='NEW', index=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('total_washer', sa.Integer, nullable=False, default=0),
        sa.Column('total_dryer', sa.Integer, nullable=False, default=0),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
    )
    
    # Create order_details table
    op.create_table(
        'order_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('status', order_detail_status_enum, nullable=False, default='NEW', index=True),
        sa.Column('machine_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('add_ons', sa.String, nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, default=0.00),
    )
    
    # Add foreign key constraints for orders table
    op.create_foreign_key('fk_orders_created_by', 'orders', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_orders_updated_by', 'orders', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_orders_deleted_by', 'orders', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_orders_store_id', 'orders', 'stores', ['store_id'], ['id'])
    
    # Add foreign key constraints for order_details table
    op.create_foreign_key('fk_order_details_created_by', 'order_details', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_order_details_updated_by', 'order_details', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_order_details_deleted_by', 'order_details', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_order_details_machine_id', 'order_details', 'machines', ['machine_id'], ['id'])
    op.create_foreign_key('fk_order_details_order_id', 'order_details', 'orders', ['order_id'], ['id'])
    
    # Create indexes for performance
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_orders_created_at', 'orders')
    
    # Drop foreign key constraints for order_details table
    op.drop_constraint('fk_order_details_order_id', 'order_details', type_='foreignkey')
    op.drop_constraint('fk_order_details_machine_id', 'order_details', type_='foreignkey')
    op.drop_constraint('fk_order_details_deleted_by', 'order_details', type_='foreignkey')
    op.drop_constraint('fk_order_details_updated_by', 'order_details', type_='foreignkey')
    op.drop_constraint('fk_order_details_created_by', 'order_details', type_='foreignkey')
    
    # Drop foreign key constraints for orders table
    op.drop_constraint('fk_orders_store_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_deleted_by', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_updated_by', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_created_by', 'orders', type_='foreignkey')
    
    # Drop tables
    op.drop_table('order_details')
    op.drop_table('orders')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS order_detail_status')
    op.execute('DROP TYPE IF EXISTS order_status')
