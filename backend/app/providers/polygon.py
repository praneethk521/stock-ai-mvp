from datetime import datetime, timezone
from typing import Any

import httpx

from app.providers.market_data import MEGA_CAP_UNIVERSE, MarketDataProvider
from app.providers.news import NewsProvider
from app.schemas.market import MarketMover, NewsArticle


class PolygonProviderError(RuntimeError):
    pass


class PolygonClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = 'https://api.polygon.io',
        timeout: float = 10.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.http_client = http_client or httpx.Client(timeout=timeout)

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {'apiKey': self.api_key, **(params or {})}
        try:
            res = self.http_client.get(f'{self.base_url}{path}', params=query)
            res.raise_for_status()
        except httpx.HTTPError as exc:
            raise PolygonProviderError(f'Polygon request failed for {path}') from exc
        data = res.json()
        status = str(data.get('status', '')).lower()
        if status in {'error', 'not_found'}:
            message = data.get('error') or data.get('message') or 'Polygon returned an error'
            raise PolygonProviderError(str(message))
        return data


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class PolygonMarketDataProvider(MarketDataProvider):
    def __init__(self, client: PolygonClient) -> None:
        self.client = client

    async def get_market_overview(self) -> dict:
        snapshots = [self._get_ticker_snapshot_sync(symbol) for symbol in ['SPY', 'QQQ', 'DIA']]
        return {
            'indices': [
                {'symbol': item['ticker'], 'change_percent': item['change_percent']}
                for item in snapshots
            ],
            'disclaimer': 'Polygon market data. Informational only. Not financial advice.',
        }

    async def get_large_cap_movers(self, min_market_cap: float = 50_000_000_000) -> list[MarketMover]:
        movers: list[MarketMover] = []
        for tracked in MEGA_CAP_UNIVERSE:
            snapshot = self._get_ticker_snapshot_sync(tracked.ticker)
            market_cap = self._get_market_cap(tracked.ticker, default=tracked.market_cap)
            if market_cap >= min_market_cap:
                movers.append(
                    MarketMover(
                        ticker=tracked.ticker,
                        company_name=tracked.company_name,
                        price=snapshot['price'],
                        change_percent=snapshot['change_percent'],
                        volume=snapshot['volume'],
                        market_cap=market_cap,
                    )
                )
        return sorted(movers, key=lambda item: abs(item.change_percent), reverse=True)

    async def get_ticker_snapshot(self, ticker: str) -> dict:
        snapshot = self._get_ticker_snapshot_sync(ticker)
        snapshot['market_cap'] = self._get_market_cap(ticker, default=snapshot['market_cap'])
        return snapshot

    def _get_ticker_snapshot_sync(self, ticker: str) -> dict:
        symbol = ticker.upper()
        data = self.client.get(f'/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}')
        result = data.get('ticker') or data.get('results') or {}
        day = result.get('day') or {}
        previous_day = result.get('prevDay') or {}
        last_trade = result.get('lastTrade') or {}

        price = _as_float(day.get('c') or last_trade.get('p') or previous_day.get('c'))
        change_percent = _as_float(result.get('todaysChangePerc'))
        if change_percent == 0.0:
            previous_close = _as_float(previous_day.get('c'))
            if previous_close:
                change_percent = ((price - previous_close) / previous_close) * 100

        return {
            'ticker': symbol,
            'price': price,
            'change_percent': round(change_percent, 3),
            'volume_change_percent': 0.0,
            'market_cap': 0.0,
            'rsi': 50.0,
            'macd_signal': 'neutral',
            'moving_average_signal': 'neutral',
            'volatility': 0.25,
            'volume': _as_int(day.get('v')),
        }

    def _get_market_cap(self, ticker: str, default: float = 0.0) -> float:
        try:
            data = self.client.get(f'/v3/reference/tickers/{ticker.upper()}')
        except PolygonProviderError:
            return default
        results = data.get('results') or {}
        return _as_float(results.get('market_cap'), default)


class PolygonNewsProvider(NewsProvider):
    def __init__(self, client: PolygonClient) -> None:
        self.client = client

    async def get_company_news(self, ticker: str) -> list[NewsArticle]:
        symbol = ticker.upper()
        data = self.client.get('/v2/reference/news', params={'ticker': symbol, 'limit': 10, 'order': 'desc'})
        articles = data.get('results') or []
        return [self._map_article(symbol, article) for article in articles]

    def _map_article(self, ticker: str, article: dict[str, Any]) -> NewsArticle:
        sentiment = self._extract_sentiment(ticker, article)
        return NewsArticle(
            ticker=ticker,
            title=str(article.get('title') or 'Untitled Polygon news article'),
            source=str((article.get('publisher') or {}).get('name') or 'Polygon News'),
            url=str(article.get('article_url') or article.get('amp_url') or ''),
            published_at=self._parse_datetime(article.get('published_utc')),
            sentiment=sentiment,
            sentiment_score={'positive': 0.65, 'neutral': 0.0, 'negative': -0.65}[sentiment],
        )

    def _extract_sentiment(self, ticker: str, article: dict[str, Any]) -> str:
        for insight in article.get('insights') or []:
            if str(insight.get('ticker', '')).upper() == ticker:
                sentiment = str(insight.get('sentiment', 'neutral')).lower()
                if sentiment in {'positive', 'neutral', 'negative'}:
                    return sentiment
        return 'neutral'

    def _parse_datetime(self, value: Any) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except ValueError:
            return datetime.now(timezone.utc)
