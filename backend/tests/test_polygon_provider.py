import json

import httpx
import pytest

from app.providers.polygon import PolygonClient, PolygonMarketDataProvider, PolygonNewsProvider, PolygonProviderError


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
