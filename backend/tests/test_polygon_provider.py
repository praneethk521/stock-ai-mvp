import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.providers.polygon import PolygonClient, PolygonMarketDataProvider, PolygonNewsProvider, PolygonProviderError


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        return self.values.get(key)

    def set(self, key: str, value: dict, ttl_seconds: int) -> None:
        self.values[key] = value


def make_client(payloads: dict[str, dict]) -> PolygonClient:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = payloads.get(request.url.path)
        if payload is None:
            return httpx.Response(404, json={'status': 'ERROR', 'error': f'No fixture for {request.url.path}'})
        return httpx.Response(200, json=payload)

    return PolygonClient(
        api_key='test-key',
        base_url='https://api.polygon.test',
        cache_ttl_seconds=30,
        retry_count=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def aggregate_path(ticker: str, days: int = 90) -> str:
    to_date = datetime.now(timezone.utc).date()
    from_date = to_date - timedelta(days=days * 2)
    return f'/v2/aggs/ticker/{ticker}/range/1/day/{from_date.isoformat()}/{to_date.isoformat()}'


def aggregate_payload(ticker: str, count: int = 60) -> dict:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return {
        'status': 'OK',
        'ticker': ticker,
        'results': [
            {
                'o': 100 + index,
                'h': 102 + index,
                'l': 99 + index,
                'c': 101 + index,
                'v': 1_000_000 + index * 10_000,
                'vw': 100.5 + index,
                'n': 50_000 + index,
                't': int((start + timedelta(days=index)).timestamp() * 1000),
            }
            for index in range(count)
        ],
    }


@pytest.mark.asyncio
async def test_polygon_market_provider_maps_snapshot_and_market_cap():
    client = make_client(
        {
            '/v2/snapshot/locale/us/markets/stocks/tickers/NVDA': {
                'status': 'OK',
                'ticker': {
                    'ticker': 'NVDA',
                    'day': {'c': 200.5, 'v': 123456},
                    'prevDay': {'c': 195.0},
                    'todaysChangePerc': 2.82,
                },
            },
            '/v3/reference/tickers/NVDA': {
                'status': 'OK',
                'results': {'market_cap': 4_800_000_000_000},
            },
            '/v1/indicators/rsi/NVDA': {
                'status': 'OK',
                'results': {'values': [{'value': 62.4}]},
            },
            '/v1/indicators/sma/NVDA': {
                'status': 'OK',
                'results': {'values': [{'value': 198.0}]},
            },
            '/v1/indicators/macd/NVDA': {
                'status': 'OK',
                'results': {'values': [{'value': 3.2, 'signal': 2.8}]},
            },
        }
    )
    provider = PolygonMarketDataProvider(client)

    snapshot = await provider.get_ticker_snapshot('nvda')

    assert snapshot['ticker'] == 'NVDA'
    assert snapshot['price'] == 200.5
    assert snapshot['change_percent'] == 2.82
    assert snapshot['volume'] == 123456
    assert snapshot['market_cap'] == 4_800_000_000_000
    assert snapshot['rsi'] == 62.4
    assert snapshot['macd_signal'] == 'bullish'
    assert snapshot['moving_average_signal'] == 'bullish'


@pytest.mark.asyncio
async def test_polygon_news_provider_maps_insight_sentiment():
    client = make_client(
        {
            '/v2/reference/news': {
                'status': 'OK',
                'results': [
                    {
                        'title': 'NVIDIA expands AI infrastructure supply',
                        'article_url': 'https://example.com/nvda',
                        'published_utc': '2026-07-07T01:00:00Z',
                        'publisher': {'name': 'Example News'},
                        'insights': [{'ticker': 'NVDA', 'sentiment': 'positive'}],
                    }
                ],
            }
        }
    )
    provider = PolygonNewsProvider(client)

    articles = await provider.get_company_news('NVDA')

    assert len(articles) == 1
    assert articles[0].source == 'Example News'
    assert articles[0].sentiment == 'positive'
    assert articles[0].sentiment_score == 0.65


def test_polygon_client_raises_on_http_error():
    client = make_client({})

    with pytest.raises(PolygonProviderError):
        client.get('/missing')


def test_polygon_client_sends_api_key():
    seen_query = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_query.update(dict(request.url.params))
        return httpx.Response(200, content=json.dumps({'status': 'OK'}))

    client = PolygonClient(
        api_key='secret-key',
        base_url='https://api.polygon.test',
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.get('/v2/reference/news', params={'ticker': 'NVDA'})

    assert seen_query['apiKey'] == 'secret-key'
    assert seen_query['ticker'] == 'NVDA'


def test_polygon_client_caches_get_responses():
    calls = {'count': 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls['count'] += 1
        return httpx.Response(200, json={'status': 'OK', 'count': calls['count']})

    client = PolygonClient(
        api_key='secret-key',
        base_url='https://api.polygon.test',
        cache_ttl_seconds=30,
        retry_count=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    first = client.get('/v1/marketstatus/now')
    second = client.get('/v1/marketstatus/now')

    assert first == second
    assert calls['count'] == 1


def test_polygon_client_uses_external_cache_backend():
    calls = {'count': 0}
    cache = FakeCache()

    def handler(request: httpx.Request) -> httpx.Response:
        calls['count'] += 1
        return httpx.Response(200, json={'status': 'OK', 'count': calls['count']})

    first_client = PolygonClient(
        api_key='secret-key',
        base_url='https://api.polygon.test',
        cache_ttl_seconds=30,
        retry_count=0,
        cache_backend=cache,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    second_client = PolygonClient(
        api_key='secret-key',
        base_url='https://api.polygon.test',
        cache_ttl_seconds=30,
        retry_count=0,
        cache_backend=cache,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    first = first_client.get('/v1/marketstatus/now')
    second = second_client.get('/v1/marketstatus/now')

    assert first == second
    assert calls['count'] == 1


def test_polygon_client_retries_transient_errors():
    calls = {'count': 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls['count'] += 1
        if calls['count'] == 1:
            return httpx.Response(503, json={'status': 'ERROR'})
        return httpx.Response(200, json={'status': 'OK'})

    client = PolygonClient(
        api_key='secret-key',
        base_url='https://api.polygon.test',
        retry_count=1,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.get('/v1/marketstatus/now') == {'status': 'OK'}
    assert calls['count'] == 2


def test_polygon_client_health_check_maps_market_status():
    client = make_client(
        {
            '/v1/marketstatus/now': {
                'status': 'OK',
                'market': 'open',
                'serverTime': '2026-07-07T13:30:00Z',
            }
        }
    )

    health = client.health_check()

    assert health == {
        'provider': 'polygon',
        'ok': True,
        'market': 'open',
        'server_time': '2026-07-07T13:30:00Z',
    }


@pytest.mark.asyncio
async def test_polygon_market_provider_maps_aggregate_candles():
    client = make_client({aggregate_path('NVDA', days=60): aggregate_payload('NVDA', count=45)})
    provider = PolygonMarketDataProvider(client)

    candles = await provider.get_historical_candles('nvda', days=60)

    assert len(candles) == 45
    assert candles[0].ticker == 'NVDA'
    assert candles[0].open == 100
    assert candles[-1].close == 145
    assert candles[-1].volume == 1_440_000


@pytest.mark.asyncio
async def test_polygon_market_provider_uses_candles_for_custom_indicators():
    client = make_client(
        {
            '/v2/snapshot/locale/us/markets/stocks/tickers/NVDA': {
                'status': 'OK',
                'ticker': {
                    'ticker': 'NVDA',
                    'day': {'c': 200.5, 'v': 123456},
                    'prevDay': {'c': 195.0},
                    'todaysChangePerc': 2.82,
                },
            },
            '/v3/reference/tickers/NVDA': {
                'status': 'OK',
                'results': {'market_cap': 4_800_000_000_000},
            },
            aggregate_path('NVDA'): aggregate_payload('NVDA', count=60),
        }
    )
    provider = PolygonMarketDataProvider(client)

    snapshot = await provider.get_ticker_snapshot('nvda')

    assert snapshot['technical_indicator_source'] == 'polygon_aggregates'
    assert snapshot['rsi'] == 100.0
    assert snapshot['macd_signal'] == 'bullish'
    assert snapshot['moving_average_signal'] == 'bullish'
    assert snapshot['volume_change_percent'] > 0


@pytest.mark.asyncio
async def test_polygon_market_provider_maps_top_market_movers():
    client = make_client(
        {
            '/v2/snapshot/locale/us/markets/stocks/gainers': {
                'status': 'OK',
                'tickers': [
                    {
                        'ticker': 'XYZ',
                        'day': {'c': 15.5, 'v': 900000},
                        'prevDay': {'c': 10.0},
                        'todaysChangePerc': 55.0,
                    }
                ],
            },
            '/v3/reference/tickers/XYZ': {
                'status': 'OK',
                'results': {'name': 'XYZ Robotics Inc', 'market_cap': 7_500_000_000},
            },
        }
    )
    provider = PolygonMarketDataProvider(client)

    movers = await provider.get_top_market_movers(direction='gainers', limit=10)

    assert len(movers) == 1
    assert movers[0].ticker == 'XYZ'
    assert movers[0].company_name == 'XYZ Robotics Inc'
    assert movers[0].price == 15.5
    assert movers[0].change_percent == 55.0
    assert movers[0].market_cap == 7_500_000_000
