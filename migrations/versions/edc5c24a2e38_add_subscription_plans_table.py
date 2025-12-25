"""add_subscription_plans_table

Revision ID: edc5c24a2e38
Revises: cdc9fba324ee
Create Date: 2025-12-26 03:37:31.581692

"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = 'edc5c24a2e38'
down_revision = 'cdc9fba324ee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    subscription_plan_interval_enum = postgresql.ENUM('MONTH', 'YEAR', name='subscription_plan_interval', create_type=False)
    subscription_plan_interval_enum.create(op.get_bind())
    subscription_plan_type_enum = postgresql.ENUM('RECURRING', 'ONE_TIME', name='subscription_plan_type', create_type=False)
    subscription_plan_type_enum.create(op.get_bind())

    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('type', subscription_plan_type_enum, nullable=False, default='RECURRING'),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('is_enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('is_default', sa.Boolean, nullable=False, default=False),
        
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('interval', subscription_plan_interval_enum, nullable=True, default='MONTH'),
        sa.Column('interval_count', sa.Integer, nullable=True, default=1),
        sa.Column('trial_period_count', sa.Integer, nullable=True, default=0),
        
        sa.Column('permission_group_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['deleted_by'], ['users.id']),
        sa.ForeignKeyConstraint(['permission_group_id'], ['permission_groups.id']),
    )


def downgrade() -> None:
    op.drop_table('subscription_plans')
