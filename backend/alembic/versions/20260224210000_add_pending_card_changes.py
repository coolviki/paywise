"""Add pending_card_changes table for card approval workflow

Revision ID: 20260224210000
Revises: 20260224201300
Create Date: 2026-02-24 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260224210000'
down_revision = '20260224201300'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pending_card_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('bank_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('banks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('existing_card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cards.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('card_type', sa.String(50), nullable=False),
        sa.Column('card_network', sa.String(50), nullable=True),
        sa.Column('annual_fee', sa.Numeric(10, 2), nullable=True),
        sa.Column('reward_type', sa.String(50), nullable=True),
        sa.Column('base_reward_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('terms_url', sa.String(500), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),  # 'new', 'update'
        sa.Column('old_values', postgresql.JSONB, nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_bank', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('scraped_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )

    # Add indexes
    op.create_index('ix_pending_card_changes_status', 'pending_card_changes', ['status'])
    op.create_index('ix_pending_card_changes_bank_id', 'pending_card_changes', ['bank_id'])


def downgrade():
    op.drop_index('ix_pending_card_changes_bank_id')
    op.drop_index('ix_pending_card_changes_status')
    op.drop_table('pending_card_changes')
