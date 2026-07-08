"""create news articles table

Revision ID: 20260707_0003
Revises: 20260706_0002
Create Date: 2026-07-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260707_0003'
down_revision = '20260706_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=12), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('source', sa.String(length=120), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sentiment', sa.String(length=16), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_hash', name='uq_news_articles_content_hash'),
    )
    op.create_index(op.f('ix_news_articles_content_hash'), 'news_articles', ['content_hash'], unique=False)
    op.create_index(op.f('ix_news_articles_id'), 'news_articles', ['id'], unique=False)
    op.create_index(op.f('ix_news_articles_provider'), 'news_articles', ['provider'], unique=False)
    op.create_index(op.f('ix_news_articles_published_at'), 'news_articles', ['published_at'], unique=False)
    op.create_index(op.f('ix_news_articles_source'), 'news_articles', ['source'], unique=False)
    op.create_index(op.f('ix_news_articles_ticker'), 'news_articles', ['ticker'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_news_articles_ticker'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_source'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_published_at'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_provider'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_id'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_content_hash'), table_name='news_articles')
    op.drop_table('news_articles')
