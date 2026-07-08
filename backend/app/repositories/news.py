from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy.orm import Session

from app.models.news import NewsArticleRecord
from app.schemas.market import NewsArticle


def persist_news_articles(
    db: Session,
    articles: list[NewsArticle],
    provider: str = 'unknown',
) -> list[NewsArticleRecord]:
    records: list[NewsArticleRecord] = []
    for article in articles:
        content_hash = build_news_content_hash(article)
        record = db.query(NewsArticleRecord).filter_by(content_hash=content_hash).one_or_none()
        now = datetime.now(timezone.utc)
        if record:
            record.sentiment = article.sentiment
            record.sentiment_score = article.sentiment_score
            record.last_seen_at = now
        else:
            record = NewsArticleRecord(
                ticker=article.ticker.upper(),
                title=article.title,
                source=article.source,
                url=article.url,
                published_at=article.published_at,
                sentiment=article.sentiment,
                sentiment_score=article.sentiment_score,
                provider=provider,
                content_hash=content_hash,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(record)
        records.append(record)
    db.commit()
    for record in records:
        db.refresh(record)
    return records


def list_recent_news_articles(
    db: Session,
    ticker: str | None = None,
    limit: int = 20,
) -> list[NewsArticleRecord]:
    query = db.query(NewsArticleRecord)
    if ticker:
        query = query.filter(NewsArticleRecord.ticker == ticker.upper())
    return query.order_by(NewsArticleRecord.published_at.desc(), NewsArticleRecord.id.desc()).limit(limit).all()


def count_news_articles(db: Session) -> int:
    return db.query(NewsArticleRecord).count()


def build_news_content_hash(article: NewsArticle) -> str:
    raw = '|'.join(
        [
            article.ticker.upper(),
            article.url.strip().lower(),
            article.title.strip().lower(),
        ]
    )
    return sha256(raw.encode('utf-8')).hexdigest()
