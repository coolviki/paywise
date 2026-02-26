"""add_campaigns

Revision ID: b2c3d4e5f6g7
Revises: 20260224210000
Create Date: 2026-02-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = '20260224210000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- campaigns ---
    op.create_table(
        'campaigns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('card_id', sa.String(36), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', sa.String(36), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('benefit_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('benefit_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('terms_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_campaigns_card_id', 'campaigns', ['card_id'])
    op.create_index('ix_campaigns_brand_id', 'campaigns', ['brand_id'])
    op.create_index('ix_campaigns_dates', 'campaigns', ['start_date', 'end_date'])

    # --- pending_campaigns ---
    op.create_table(
        'pending_campaigns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('card_id', sa.String(36), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', sa.String(36), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('benefit_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('benefit_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('terms_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('existing_campaign_id', sa.String(36), sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('scraped_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('reviewed_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_pending_campaigns_status', 'pending_campaigns', ['status'])


def downgrade() -> None:
    op.drop_index('ix_pending_campaigns_status', table_name='pending_campaigns')
    op.drop_table('pending_campaigns')
    op.drop_index('ix_campaigns_dates', table_name='campaigns')
    op.drop_index('ix_campaigns_brand_id', table_name='campaigns')
    op.drop_index('ix_campaigns_card_id', table_name='campaigns')
    op.drop_table('campaigns')
