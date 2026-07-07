"""create watchlist items table

Revision ID: 20260706_0002
Revises: 20260701_0001
Create Date: 2026-07-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260706_0002'
down_revision = '20260701_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=12), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker', name='uq_watchlist_items_ticker'),
    )
    op.create_index(op.f('ix_watchlist_items_id'), 'watchlist_items', ['id'], unique=False)
    op.create_index(op.f('ix_watchlist_items_ticker'), 'watchlist_items', ['ticker'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_watchlist_items_ticker'), table_name='watchlist_items')
    op.drop_index(op.f('ix_watchlist_items_id'), table_name='watchlist_items')
    op.drop_table('watchlist_items')
