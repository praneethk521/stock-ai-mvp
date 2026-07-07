from abc import ABC, abstractmethod
from datetime import datetime, timezone
from app.schemas.market import NewsArticle


class NewsProvider(ABC):
    @abstractmethod
    async def get_company_news(self, ticker: str) -> list[NewsArticle]: ...


class MockNewsProvider(NewsProvider):
    async def get_company_news(self, ticker: str) -> list[NewsArticle]:
        symbol = ticker.upper()
        now = datetime.now(timezone.utc)
        mock_news = {
            'NVDA': [
                ('NVIDIA demand remains strong as AI infrastructure spending expands', 'positive', 0.78),
                ('Chip supply constraints remain a watch item for NVIDIA buyers', 'neutral', 0.12),
            ],
            'TSLA': [
                ('Tesla shares move higher after delivery optimism improves', 'positive', 0.64),
                ('Margin pressure remains a concern for Tesla investors', 'negative', -0.38),
            ],
            'AAPL': [
                ('Apple services revenue continues to support investor sentiment', 'positive', 0.42),
                ('Analysts debate iPhone upgrade cycle timing', 'neutral', 0.05),
            ],
            'MSFT': [
                ('Microsoft cloud growth remains resilient with AI demand', 'positive', 0.66),
                ('Enterprise software spending scrutiny keeps estimates balanced', 'neutral', 0.08),
            ],
            'AMZN': [
                ('Amazon retail margins improve while AWS demand stabilizes', 'positive', 0.48),
                ('Logistics costs remain a swing factor for Amazon outlook', 'neutral', -0.04),
            ],
            'META': [
                ('Meta advertising trends improve across major markets', 'positive', 0.52),
                ('Investors monitor AI capex and metaverse spending', 'neutral', 0.02),
            ],
            'AVGO': [
                ('Broadcom rallies as AI networking demand strengthens', 'positive', 0.71),
                ('Valuation questions rise after recent Broadcom gains', 'neutral', 0.01),
            ],
            'TSM': [
                ('TSMC advanced node demand remains constructive', 'positive', 0.46),
                ('Geopolitical risk weighs on semiconductor sentiment', 'negative', -0.44),
            ],
            'GOOG': [
                ('Alphabet search and cloud trends support bullish commentary', 'positive', 0.55),
                ('AI competition keeps Alphabet margin debate active', 'neutral', -0.02),
            ],
            'BRK.B': [
                ('Berkshire Hathaway remains steady as defensive demand holds', 'neutral', 0.18),
                ('Insurance results support Berkshire investor confidence', 'positive', 0.37),
            ],
        }
        items = mock_news.get(symbol, [(f'{symbol} reports stronger demand and positive analyst commentary', 'positive', 0.72)])
        return [
            NewsArticle(
                ticker=symbol,
                title=title,
                source='Mock Finance News',
                url=f'https://example.com/mock-news/{symbol.lower()}',
                published_at=now,
                sentiment=sentiment,
                sentiment_score=score,
            )
            for title, sentiment, score in items
        ]
