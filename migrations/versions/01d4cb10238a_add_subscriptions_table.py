"""add_subscriptions_table

Revision ID: 01d4cb10238a
Revises: edc5c24a2e38
Create Date: 2025-12-26 15:19:33.215588

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '01d4cb10238a'
down_revision = 'edc5c24a2e38'
branch_labels = None
depends_on = None


def upgrade() -> None:
    subscription_status_enum = postgresql.ENUM(
        'ACTIVE', 'CANCELLED', 'PAST_DUE', 'EXPIRED',
        name='subscription_status', create_type=False)
    subscription_status_enum.create(op.get_bind())

    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('subscription_plan_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        
        sa.Column('status', subscription_status_enum, nullable=False, default='ACTIVE', index=True),
        
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_renewal_date', sa.DateTime(timezone=True), nullable=True),
        
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['subscription_plan_id'], ['subscription_plans.id']),
    )


def downgrade() -> None:
    op.drop_table('subscriptions')
