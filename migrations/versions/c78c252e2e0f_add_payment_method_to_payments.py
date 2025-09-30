"""add_payment_method_to_payments

Revision ID: c78c252e2e0f
Revises: cb9ab276e0bd
Create Date: 2025-10-01 01:23:50.187899

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c78c252e2e0f'
down_revision = 'cb9ab276e0bd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_method enum type
    payment_method_enum = postgresql.ENUM(
        'QR', 'CARD', 'OTHER',
        name='payment_method',
        create_type=False
    )
    payment_method_enum.create(op.get_bind())
    
    # Add payment_method column to payments table
    op.add_column('payments', 
        sa.Column('payment_method', 
            postgresql.ENUM('QR', 'CARD', 'OTHER', name='payment_method', create_type=False), 
            nullable=False, 
            server_default='QR'
        )
    )
    
    # Create index for payment_method column
    op.create_index(op.f('ix_payments_payment_method'), 'payments', ['payment_method'], unique=False)


def downgrade() -> None:
    # Drop index for payment_method column
    op.drop_index(op.f('ix_payments_payment_method'), table_name='payments')
    
    # Drop payment_method column from payments table
    op.drop_column('payments', 'payment_method')
    
    # Drop payment_method enum type
    op.execute('DROP TYPE payment_method')
