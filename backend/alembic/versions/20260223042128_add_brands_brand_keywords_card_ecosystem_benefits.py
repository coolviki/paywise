"""add_brands_brand_keywords_card_ecosystem_benefits

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-02-23 04:21:28.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- brands ---
    op.create_table(
        'brands',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # --- brand_keywords ---
    op.create_table(
        'brand_keywords',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('brand_id', sa.String(36), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_brand_keywords_keyword', 'brand_keywords', ['keyword'])

    # --- card_ecosystem_benefits ---
    op.create_table(
        'card_ecosystem_benefits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('card_id', sa.String(36), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand_id', sa.String(36), sa.ForeignKey('brands.id', ondelete='CASCADE'), nullable=False),
        sa.Column('benefit_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('benefit_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_card_ecosystem_benefits_card_id', 'card_ecosystem_benefits', ['card_id'])
    op.create_index('ix_card_ecosystem_benefits_brand_id', 'card_ecosystem_benefits', ['brand_id'])


def downgrade() -> None:
    op.drop_table('card_ecosystem_benefits')
    op.drop_index('ix_brand_keywords_keyword', table_name='brand_keywords')
    op.drop_table('brand_keywords')
    op.drop_table('brands')
