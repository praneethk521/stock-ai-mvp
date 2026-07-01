from app.providers.market_data import MockMarketDataProvider, MarketDataProvider
from app.providers.news import MockNewsProvider, NewsProvider


def get_market_provider() -> MarketDataProvider:
    return MockMarketDataProvider()


def get_news_provider() -> NewsProvider:
    return MockNewsProvider()
