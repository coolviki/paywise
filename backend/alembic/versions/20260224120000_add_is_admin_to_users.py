"""Add is_admin column to users table

Revision ID: 20260224120000
Revises: 20260223042128
Create Date: 2026-02-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260224120000'
down_revision = '20260223042128'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('users', 'is_admin')
