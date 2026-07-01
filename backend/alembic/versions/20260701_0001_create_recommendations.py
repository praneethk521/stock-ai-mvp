"""create recommendations table

Revision ID: 20260701_0001
Revises:
Create Date: 2026-07-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260701_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=12), nullable=False),
        sa.Column('recommendation', sa.String(length=16), nullable=False),
        sa.Column('trade_horizon', sa.String(length=16), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('explanation', sa.String(length=2000), nullable=False),
        sa.Column('supporting_signals', sa.JSON(), nullable=False),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_recommendations_ticker'), 'recommendations', ['ticker'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_recommendations_ticker'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_id'), table_name='recommendations')
    op.drop_table('recommendations')
