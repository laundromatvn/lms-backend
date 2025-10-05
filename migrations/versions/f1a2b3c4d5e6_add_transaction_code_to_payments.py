"""add_transaction_code_to_payments

Revision ID: f1a2b3c4d5e6
Revises: 5f908d78f3c2
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import string
import random


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '5f908d78f3c2'
branch_labels = None
depends_on = None


def _generate_transaction_code() -> str:
    """
    Generate a unique 8-character transaction code.
    
    The code contains uppercase letters and digits, with at least one letter and one digit.
    """
    # Generate 8 characters with at least one letter and one digit
    letters = string.ascii_uppercase
    digits = string.digits

    code = [
        random.choice(letters),
        random.choice(digits)
    ]
    
    for _ in range(6):
        code.append(random.choice(letters + digits))
    
    random.shuffle(code)
    return ''.join(code)


def upgrade() -> None:
    # Add transaction_code column to payments table as nullable first
    op.add_column('payments', 
        sa.Column('transaction_code', sa.String(8), nullable=True)
    )

    # Get connection to execute raw SQL
    connection = op.get_bind()
    
    # Get all existing payment records
    result = connection.execute(sa.text("SELECT id FROM payments WHERE transaction_code IS NULL"))
    payment_ids = [row[0] for row in result]
    
    # Generate unique transaction codes for existing payments
    used_codes = set()
    for payment_id in payment_ids:
        while True:
            code = _generate_transaction_code()
            if code not in used_codes:
                # Check if code already exists in database
                existing = connection.execute(
                    sa.text("SELECT id FROM payments WHERE transaction_code = :code"),
                    {"code": code}
                ).fetchone()
                if not existing:
                    used_codes.add(code)
                    # Update the payment record with the transaction code
                    connection.execute(
                        sa.text("UPDATE payments SET transaction_code = :code WHERE id = :payment_id"),
                        {"code": code, "payment_id": payment_id}
                    )
                    break
    
    # Now make the column NOT NULL
    op.alter_column('payments', 'transaction_code', nullable=False)

    # Create index on transaction_code for efficient lookups
    op.create_index('ix_payments_transaction_code', 'payments', ['transaction_code'])
    
    # Create unique constraint on transaction_code
    op.create_unique_constraint('uq_payments_transaction_code', 'payments', ['transaction_code'])


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint('uq_payments_transaction_code', 'payments', type_='unique')
    
    # Drop index
    op.drop_index('ix_payments_transaction_code', 'payments')
    
    # Drop transaction_code column from payments table
    op.drop_column('payments', 'transaction_code')
