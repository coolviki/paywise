"""Add terms_url column to cards table

Revision ID: 20260224201300
Revises: 20260224150000
Create Date: 2026-02-24 20:13:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260224201300'
down_revision = '20260224150000'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cards', sa.Column('terms_url', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('cards', 'terms_url')
