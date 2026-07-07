from app.core.config import get_settings
from app.core.cache import JsonCache
from app.providers.market_data import MockMarketDataProvider, MarketDataProvider
from app.providers.news import MockNewsProvider, NewsProvider
from app.providers.polygon import PolygonClient, PolygonMarketDataProvider, PolygonNewsProvider


settings = get_settings()


def get_polygon_client() -> PolygonClient:
    if not settings.polygon_api_key:
        raise ValueError('POLYGON_API_KEY is required when using Polygon providers')
    cache_backend = JsonCache(settings.redis_url) if settings.redis_url else None
    return PolygonClient(
        api_key=settings.polygon_api_key,
        base_url=settings.polygon_base_url,
        timeout=settings.provider_timeout_seconds,
        cache_ttl_seconds=settings.provider_cache_ttl_seconds,
        retry_count=settings.provider_retry_count,
        cache_backend=cache_backend,
    )


def get_market_provider() -> MarketDataProvider:
    if settings.market_data_provider == 'polygon':
        return PolygonMarketDataProvider(get_polygon_client())
    return MockMarketDataProvider()


def get_news_provider() -> NewsProvider:
    if settings.news_provider == 'polygon':
        return PolygonNewsProvider(get_polygon_client())
    return MockNewsProvider()
