from abc import ABC, abstractmethod
from datetime import datetime, timezone
from app.schemas.market import NewsArticle


class NewsProvider(ABC):
    @abstractmethod
    async def get_company_news(self, ticker: str) -> list[NewsArticle]: ...


class MockNewsProvider(NewsProvider):
    async def get_company_news(self, ticker: str) -> list[NewsArticle]:
        return [
            NewsArticle(
                ticker=ticker.upper(),
                title=f'{ticker.upper()} reports stronger demand and positive analyst commentary',
                source='Mock Finance News',
                url='https://example.com/mock-news',
                published_at=datetime.now(timezone.utc),
                sentiment='positive',
                sentiment_score=0.72,
            )
        ]
