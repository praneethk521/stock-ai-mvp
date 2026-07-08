"""add user scope to recommendations and watchlist

Revision ID: 20260707_0005
Revises: 20260707_0004
Create Date: 2026-07-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260707_0005'
down_revision = '20260707_0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('recommendations', sa.Column('user_id', sa.String(length=64), nullable=False, server_default='local-demo-user'))
    op.add_column('watchlist_items', sa.Column('user_id', sa.String(length=64), nullable=False, server_default='local-demo-user'))
    op.create_index(op.f('ix_recommendations_user_id'), 'recommendations', ['user_id'], unique=False)
    op.create_index(op.f('ix_watchlist_items_user_id'), 'watchlist_items', ['user_id'], unique=False)
    op.drop_constraint('uq_watchlist_items_ticker', 'watchlist_items', type_='unique')
    op.create_unique_constraint('uq_watchlist_items_user_ticker', 'watchlist_items', ['user_id', 'ticker'])
    op.alter_column('recommendations', 'user_id', server_default=None)
    op.alter_column('watchlist_items', 'user_id', server_default=None)


def downgrade() -> None:
    op.drop_constraint('uq_watchlist_items_user_ticker', 'watchlist_items', type_='unique')
    op.create_unique_constraint('uq_watchlist_items_ticker', 'watchlist_items', ['ticker'])
    op.drop_index(op.f('ix_watchlist_items_user_id'), table_name='watchlist_items')
    op.drop_index(op.f('ix_recommendations_user_id'), table_name='recommendations')
    op.drop_column('watchlist_items', 'user_id')
    op.drop_column('recommendations', 'user_id')
