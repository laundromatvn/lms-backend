"""create_payment_tables

Revision ID: cb9ab276e0bd
Revises: fedcba987654
Create Date: 2025-10-01 00:07:39.656362

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'cb9ab276e0bd'
down_revision = 'e95e621f70aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_status enum type
    payment_status_enum = postgresql.ENUM(
        'NEW', 'WAITING_FOR_PAYMENT_DETAIL', 'WAITING_FOR_PURCHASE', 
        'SUCCESS', 'FAILED', 'CANCELLED',
        name='payment_status',
        create_type=False
    )
    payment_status_enum.create(op.get_bind())
    
    # Create payment_provider enum type
    payment_provider_enum = postgresql.ENUM(
        'VIET_QR',
        name='payment_provider',
        create_type=False
    )
    payment_provider_enum.create(op.get_bind())
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('NEW', 'WAITING_FOR_PAYMENT_DETAIL', 'WAITING_FOR_PURCHASE', 'SUCCESS', 'FAILED', 'CANCELLED', name='payment_status', create_type=False), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('provider', postgresql.ENUM('VIET_QR', name='payment_provider', create_type=False), nullable=False),
        sa.Column('provider_transaction_id', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_payments_created_by'), 'payments', ['created_by'], unique=False)
    op.create_index(op.f('ix_payments_deleted_by'), 'payments', ['deleted_by'], unique=False)
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_provider'), 'payments', ['provider'], unique=False)
    op.create_index(op.f('ix_payments_provider_transaction_id'), 'payments', ['provider_transaction_id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_store_id'), 'payments', ['store_id'], unique=False)
    op.create_index(op.f('ix_payments_tenant_id'), 'payments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_payments_updated_by'), 'payments', ['updated_by'], unique=False)
    
    # Create composite index for common queries
    op.create_index('ix_payments_store_status', 'payments', ['store_id', 'status'], unique=False)
    
    # Create foreign key constraints
    op.create_foreign_key('fk_payments_created_by_users', 'payments', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_payments_deleted_by_users', 'payments', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_payments_order_id_orders', 'payments', 'orders', ['order_id'], ['id'])
    op.create_foreign_key('fk_payments_store_id_stores', 'payments', 'stores', ['store_id'], ['id'])
    op.create_foreign_key('fk_payments_tenant_id_tenants', 'payments', 'tenants', ['tenant_id'], ['id'])
    op.create_foreign_key('fk_payments_updated_by_users', 'payments', 'users', ['updated_by'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_payments_updated_by_users', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_tenant_id_tenants', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_store_id_stores', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_order_id_orders', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_deleted_by_users', 'payments', type_='foreignkey')
    op.drop_constraint('fk_payments_created_by_users', 'payments', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_payments_store_status', table_name='payments')
    op.drop_index(op.f('ix_payments_updated_by'), table_name='payments')
    op.drop_index(op.f('ix_payments_tenant_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_store_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_provider_transaction_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_provider'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_deleted_by'), table_name='payments')
    op.drop_index(op.f('ix_payments_created_by'), table_name='payments')
    
    # Drop table
    op.drop_table('payments')
    
    # Drop enum types
    op.execute('DROP TYPE payment_provider')
    op.execute('DROP TYPE payment_status')
