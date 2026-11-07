"""add_mcp_api_keys

Personal API keys for the Claude MCP connector.

Revision ID: 20261107_mcp_keys
Revises: b2c3d4e5f6g7
Create Date: 2026-11-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20261107_mcp_keys'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mcp_api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_prefix', sa.String(16), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_mcp_api_keys_user_id', 'mcp_api_keys', ['user_id'])
    op.create_index('ix_mcp_api_keys_key_hash', 'mcp_api_keys', ['key_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_mcp_api_keys_key_hash', table_name='mcp_api_keys')
    op.drop_index('ix_mcp_api_keys_user_id', table_name='mcp_api_keys')
    op.drop_table('mcp_api_keys')
