"""add_firmware_table

Revision ID: cf12a3f0158b
Revises: 2ce4a8a035b0
Create Date: 2025-11-10 11:12:03.304644

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'cf12a3f0158b'
down_revision = '2ce4a8a035b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create firmware_status enum type
    firmware_status_enum = postgresql.ENUM(
        'DRAFT', 'RELEASED', 'OUT_OF_DATE', 'DEPRECATED',
        name='firmware_status',
        create_type=False
    )
    firmware_status_enum.create(op.get_bind())
    
    # Create firmware_version_type enum type

    firmware_version_type_enum = postgresql.ENUM(
        'MAJOR', 'MINOR', 'PATCH',
        name='firmware_version_type',
        create_type=False
    )
    firmware_version_type_enum.create(op.get_bind())
    
    # Create firmwares table

    op.create_table(
        'firmwares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('version', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('status', firmware_status_enum, nullable=False, default='DRAFT', server_default='DRAFT', index=True),
        sa.Column('version_type', firmware_version_type_enum, nullable=False, default='PATCH', server_default='PATCH', index=True),
        sa.Column('object_name', sa.String(255), nullable=False, index=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(128), nullable=False),
    )

    # Add foreign key constraints
    op.create_foreign_key('fk_firmwares_created_by', 'firmwares', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_firmwares_updated_by', 'firmwares', 'users', ['updated_by'], ['id'])
    op.create_foreign_key('fk_firmwares_deleted_by', 'firmwares', 'users', ['deleted_by'], ['id'])

def downgrade() -> None:
    # Drop the table (this automatically drops all constraints)
    op.drop_table('firmwares')

    # Drop the enum types
    op.execute('DROP TYPE IF EXISTS firmware_status')
    op.execute('DROP TYPE IF EXISTS firmware_version_type')


