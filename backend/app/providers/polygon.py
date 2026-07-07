from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Any

import httpx
import structlog

from app.providers.market_data import MEGA_CAP_UNIVERSE, MarketDataProvider
from app.providers.news import NewsProvider
from app.schemas.market import MarketMover, NewsArticle


logger = structlog.get_logger(__name__)


class PolygonProviderError(RuntimeError):
    pass


class PolygonClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = 'https://api.polygon.io',
        timeout: float = 10.0,
        cache_ttl_seconds: int = 30,
        retry_count: int = 2,
        http_client: httpx.Client | None = None,
        cache_backend: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.cache_ttl_seconds = cache_ttl_seconds
        self.retry_count = retry_count
        self.http_client = http_client or httpx.Client(timeout=timeout)
        self.cache_backend = cache_backend
        self._cache: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[datetime, dict[str, Any]]] = {}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {'apiKey': self.api_key, **(params or {})}
        cache_key = self._cache_key(path, query)
        cache_label = self._cache_label(path, query)
        started_at = datetime.now(timezone.utc)

        backend_cached = self.cache_backend.get(cache_label) if self.cache_backend and self.cache_ttl_seconds > 0 else None
        if backend_cached:
            self._log_request(path, 'cache', 200, started_at, cache_hit=True, cache_backend='redis')
            return backend_cached

        cached = self._cache.get(cache_key)
        if cached and cached[0] > datetime.now(timezone.utc):
            self._log_request(path, 'cache', 200, started_at, cache_hit=True, cache_backend='memory')
            return cached[1]

        last_error: httpx.HTTPError | None = None
        for attempt in range(self.retry_count + 1):
            try:
                res = self.http_client.get(f'{self.base_url}{path}', params=query)
                if res.status_code in {429, 500, 502, 503, 504} and attempt < self.retry_count:
                    self._log_request(path, 'retry', res.status_code, started_at, attempt=attempt + 1)
                    sleep(0.2 * (attempt + 1))
                    continue
                res.raise_for_status()
                data = res.json()
                self._log_request(path, 'network', res.status_code, started_at, cache_hit=False, attempt=attempt + 1)
                break
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.retry_count:
                    status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
                    self._log_request(path, 'retry', status_code, started_at, attempt=attempt + 1, error=str(exc))
                    sleep(0.2 * (attempt + 1))
                    continue
                self._log_request(path, 'failed', None, started_at, attempt=attempt + 1, error=str(exc))
                raise PolygonProviderError(f'Polygon request failed for {path}') from exc
        else:
            raise PolygonProviderError(f'Polygon request failed for {path}') from last_error

        status = str(data.get('status', '')).lower()
        if status in {'error', 'not_found'}:
            message = data.get('error') or data.get('message') or 'Polygon returned an error'
            raise PolygonProviderError(str(message))
        if self.cache_ttl_seconds > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl_seconds)
            self._cache[cache_key] = (expires_at, data)
            if self.cache_backend:
                self.cache_backend.set(cache_label, data, self.cache_ttl_seconds)
        return data

    def health_check(self) -> dict[str, Any]:
        data = self.get('/v1/marketstatus/now')
        return {
            'provider': 'polygon',
            'ok': True,
            'market': data.get('market'),
            'server_time': data.get('serverTime'),
        }

    def _cache_key(self, path: str, query: dict[str, Any]) -> tuple[str, tuple[tuple[str, str], ...]]:
        normalized = tuple(sorted((key, str(value)) for key, value in query.items()))
        return path, normalized

    def _cache_label(self, path: str, query: dict[str, Any]) -> str:
        normalized = tuple(sorted((key, str(value)) for key, value in query.items()))
        return f'{path}:{normalized}'

    def _log_request(
        self,
        path: str,
        source: str,
        status_code: int | None,
        started_at: datetime,
        **extra: Any,
    ) -> None:
        duration_ms = round((datetime.now(timezone.utc) - started_at).total_seconds() * 1000, 2)
        logger.info(
            'polygon_request',
            path=path,
            source=source,
            status_code=status_code,
            duration_ms=duration_ms,
            **extra,
        )


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

    async def get_top_market_movers(self, direction: str = 'gainers', limit: int = 10) -> list[MarketMover]:
        data = self.client.get(f'/v2/snapshot/locale/us/markets/stocks/{direction}', params={'include_otc': 'false'})
        results = data.get('tickers') or data.get('results') or []
        movers: list[MarketMover] = []
        for result in results[:limit]:
            symbol = str(result.get('ticker') or '').upper()
            if not symbol:
                continue
            company_name, market_cap = self._get_company_reference(symbol)
            movers.append(self._map_snapshot_mover(result, company_name=company_name, market_cap=market_cap))
        return movers

    async def get_ticker_snapshot(self, ticker: str) -> dict:
        snapshot = self._get_ticker_snapshot_sync(ticker)
        snapshot['market_cap'] = self._get_market_cap(ticker, default=snapshot['market_cap'])
        snapshot.update(self._get_technical_indicators(ticker, price=snapshot['price']))
        return snapshot

    def health_check(self) -> dict[str, Any]:
        return self.client.health_check()

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

    def _get_company_reference(self, ticker: str) -> tuple[str, float]:
        try:
            data = self.client.get(f'/v3/reference/tickers/{ticker.upper()}')
        except PolygonProviderError:
            return ticker.upper(), 0.0
        results = data.get('results') or {}
        return str(results.get('name') or ticker.upper()), _as_float(results.get('market_cap'))

    def _map_snapshot_mover(self, result: dict[str, Any], company_name: str, market_cap: float) -> MarketMover:
        day = result.get('day') or {}
        previous_day = result.get('prevDay') or {}
        last_trade = result.get('lastTrade') or {}
        price = _as_float(day.get('c') or last_trade.get('p') or previous_day.get('c'))
        change_percent = _as_float(result.get('todaysChangePerc'))
        if change_percent == 0.0:
            previous_close = _as_float(previous_day.get('c'))
            if previous_close:
                change_percent = ((price - previous_close) / previous_close) * 100
        return MarketMover(
            ticker=str(result.get('ticker') or '').upper(),
            company_name=company_name,
            price=price,
            change_percent=round(change_percent, 3),
            volume=_as_int(day.get('v')),
            market_cap=market_cap,
        )

    def _get_technical_indicators(self, ticker: str, price: float) -> dict[str, Any]:
        symbol = ticker.upper()
        rsi = self._get_latest_indicator_value(f'/v1/indicators/rsi/{symbol}', default=50.0)
        sma = self._get_latest_indicator_value(f'/v1/indicators/sma/{symbol}', params={'window': 50}, default=0.0)
        macd_payload = self._get_latest_indicator(f'/v1/indicators/macd/{symbol}')
        macd_value = _as_float(macd_payload.get('value'))
        macd_signal_value = _as_float(macd_payload.get('signal'))
        return {
            'rsi': rsi,
            'macd_signal': self._macd_signal(macd_payload, macd_value, macd_signal_value),
            'moving_average_signal': 'bullish' if sma and price >= sma else 'bearish' if sma else 'neutral',
        }

    def _macd_signal(self, payload: dict[str, Any], value: float, signal: float) -> str:
        if not payload:
            return 'neutral'
        return 'bullish' if value >= signal else 'bearish'

    def _get_latest_indicator_value(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        default: float = 0.0,
    ) -> float:
        payload = self._get_latest_indicator(path, params=params)
        return _as_float(payload.get('value'), default)

    def _get_latest_indicator(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = {
            'timespan': 'day',
            'adjusted': 'true',
            'series_type': 'close',
            'order': 'desc',
            'limit': 1,
            **(params or {}),
        }
        try:
            data = self.client.get(path, params=query)
        except PolygonProviderError:
            return {}
        values = ((data.get('results') or {}).get('values') or [])
        return values[0] if values else {}


class PolygonNewsProvider(NewsProvider):
    def __init__(self, client: PolygonClient) -> None:
        self.client = client

    async def get_company_news(self, ticker: str) -> list[NewsArticle]:
        symbol = ticker.upper()
        data = self.client.get('/v2/reference/news', params={'ticker': symbol, 'limit': 10, 'order': 'desc'})
        articles = data.get('results') or []
        return [self._map_article(symbol, article) for article in articles]

    def health_check(self) -> dict[str, Any]:
        return self.client.health_check()

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
