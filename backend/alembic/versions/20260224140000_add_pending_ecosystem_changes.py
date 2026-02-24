"""Add pending_ecosystem_changes table for scraper approval workflow

Revision ID: 20260224140000
Revises: 20260224120000
Create Date: 2026-02-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260224140000'
down_revision = '20260224120000'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pending_ecosystem_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('benefit_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('benefit_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),  # 'new', 'update', 'delete'
        sa.Column('old_values', postgresql.JSONB, nullable=True),  # For updates, store previous values
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'approved', 'rejected'
        sa.Column('scraped_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # Add indexes for common queries
    op.create_index('ix_pending_ecosystem_changes_status', 'pending_ecosystem_changes', ['status'])
    op.create_index('ix_pending_ecosystem_changes_card_id', 'pending_ecosystem_changes', ['card_id'])
    op.create_index('ix_pending_ecosystem_changes_brand_id', 'pending_ecosystem_changes', ['brand_id'])


def downgrade():
    op.drop_index('ix_pending_ecosystem_changes_brand_id')
    op.drop_index('ix_pending_ecosystem_changes_card_id')
    op.drop_index('ix_pending_ecosystem_changes_status')
    op.drop_table('pending_ecosystem_changes')
