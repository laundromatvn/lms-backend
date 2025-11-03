"""add_promotion_campaign_table

Revision ID: 952f199511f3
Revises: bfc1ed69cab5
Create Date: 2025-11-02 11:30:56.629814

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '952f199511f3'
down_revision = 'bfc1ed69cab5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promotion_campaign_status enum type
    promotion_campaign_status_enum = postgresql.ENUM(
        'DRAFT', 'SCHEDULED', 'ACTIVE', 'PAUSED', 'INACTIVE',
        name='promotion_campaign_status',
        create_type=False
    )
    promotion_campaign_status_enum.create(op.get_bind())
    
    # Create promotion_campaigns table
    op.create_table(
        'promotion_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', promotion_campaign_status_enum, nullable=False, default='DRAFT', server_default='DRAFT', index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('conditions', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('rewards', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('limits', postgresql.JSON, nullable=False, server_default='[]'),
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_promotion_campaigns_created_by', 'promotion_campaigns', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_promotion_campaigns_updated_by', 'promotion_campaigns', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_promotion_campaigns_deleted_by', 'promotion_campaigns', 'users', ['deleted_by'], ['id'])
    op.create_foreign_key('fk_promotion_campaigns_tenant_id', 'promotion_campaigns', 'tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_promotion_campaigns_deleted_by', 'promotion_campaigns', type_='foreignkey')
    op.drop_constraint('fk_promotion_campaigns_updated_by', 'promotion_campaigns', type_='foreignkey')
    op.drop_constraint('fk_promotion_campaigns_created_by', 'promotion_campaigns', type_='foreignkey')
    op.drop_constraint('fk_promotion_campaigns_tenant_id', 'promotion_campaigns', type_='foreignkey')

    # Drop table
    op.drop_table('promotion_campaigns')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS promotion_campaign_status')
