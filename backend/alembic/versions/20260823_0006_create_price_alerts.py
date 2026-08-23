"""create price alerts

Revision ID: 20260823_0006
Revises: 20260707_0005
Create Date: 2026-08-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260823_0006'
down_revision = '20260707_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('ticker', sa.String(length=12), nullable=False),
        sa.Column('condition', sa.String(length=8), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_price', sa.Float(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("condition IN ('above', 'below')", name='ck_price_alerts_condition'),
        sa.CheckConstraint('target_price > 0 AND target_price <= 1000000000', name='ck_price_alerts_target_price'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_price_alerts_id'), 'price_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_price_alerts_ticker'), 'price_alerts', ['ticker'], unique=False)
    op.create_index(op.f('ix_price_alerts_user_id'), 'price_alerts', ['user_id'], unique=False)
    op.create_index('ix_price_alerts_user_active', 'price_alerts', ['user_id', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_price_alerts_user_active', table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_user_id'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_ticker'), table_name='price_alerts')
    op.drop_index(op.f('ix_price_alerts_id'), table_name='price_alerts')
    op.drop_table('price_alerts')
