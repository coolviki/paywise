"""Add pending_brand_changes table for brand approval workflow

Revision ID: 20260224150000
Revises: 20260224140000
Create Date: 2026-02-24 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260224150000'
down_revision = '20260224140000'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pending_brand_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('keywords', postgresql.JSONB, nullable=True),  # Array of keywords
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_bank', sa.String(50), nullable=True),  # hdfc, icici, sbi
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'approved', 'rejected'
        sa.Column('scraped_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # Add index for status
    op.create_index('ix_pending_brand_changes_status', 'pending_brand_changes', ['status'])


def downgrade():
    op.drop_index('ix_pending_brand_changes_status')
    op.drop_table('pending_brand_changes')
