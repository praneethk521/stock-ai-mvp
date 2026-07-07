from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app
from app.models.recommendation import RecommendationRecord


engine = create_engine(
    'sqlite://',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_large_cap_movers_returns_top_ten_sorted_by_absolute_move():
    reset_db()
    res = client.get('/api/v1/market/large-cap-movers')

    assert res.status_code == 200
    items = res.json()['items']
    assert len(items) == 10
    assert items[0]['ticker'] == 'TSLA'
    assert abs(items[0]['change_percent']) >= abs(items[-1]['change_percent'])


def test_top_market_movers_returns_gainers_and_losers():
    reset_db()

    gainers_res = client.get('/api/v1/market/top-movers?direction=gainers&limit=3')
    losers_res = client.get('/api/v1/market/top-movers?direction=losers&limit=3')

    assert gainers_res.status_code == 200
    assert losers_res.status_code == 200
    gainers = gainers_res.json()['items']
    losers = losers_res.json()['items']
    assert len(gainers) == 3
    assert len(losers) == 3
    assert gainers[0]['change_percent'] >= gainers[-1]['change_percent']
    assert losers[0]['change_percent'] <= losers[-1]['change_percent']


def test_top_market_movers_rejects_invalid_direction():
    reset_db()

    res = client.get('/api/v1/market/top-movers?direction=flat')

    assert res.status_code == 400
    error = res.json()['error']
    assert error['code'] == 'bad_request'
    assert error['message'] == 'Direction must be gainers or losers'
    assert error['request_id']


def test_stock_recommendation_accepts_class_share_ticker():
    reset_db()
    res = client.get('/api/v1/stocks/BRK.B/recommendation')

    assert res.status_code == 200
    assert res.json()['ticker'] == 'BRK.B'

    with TestingSessionLocal() as db:
        saved = db.query(RecommendationRecord).filter_by(ticker='BRK.B').one()
        assert saved.recommendation == res.json()['recommendation']


def test_stock_candles_returns_bounded_history():
    reset_db()

    res = client.get('/api/v1/stocks/NVDA/candles?days=30')

    assert res.status_code == 200
    candles = res.json()
    assert len(candles) == 30
    assert candles[0]['ticker'] == 'NVDA'
    assert {'open', 'high', 'low', 'close', 'volume'} <= set(candles[0].keys())


def test_recent_recommendations_returns_persisted_history():
    reset_db()
    client.get('/api/v1/stocks/NVDA/recommendation')
    client.get('/api/v1/stocks/TSLA/recommendation')

    res = client.get('/api/v1/recommendations/recent?limit=1')

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]['ticker'] == 'TSLA'
    assert items[0]['model_version'] == 'rules-v1'


def test_recent_recommendations_filters_by_ticker():
    reset_db()
    client.get('/api/v1/stocks/NVDA/recommendation')
    client.get('/api/v1/stocks/TSLA/recommendation')

    res = client.get('/api/v1/recommendations/recent?ticker=NVDA')

    assert res.status_code == 200
    assert [item['ticker'] for item in res.json()] == ['NVDA']


def test_admin_status_includes_persistence_count():
    reset_db()
    client.get('/api/v1/stocks/NVDA/recommendation')

    res = client.get('/api/v1/admin/status')

    assert res.status_code == 200
    data = res.json()
    assert data['market_data_provider'] == 'mock'
    assert data['market_provider_health']['ok'] is True
    assert data['news_provider_health']['ok'] is True
    assert data['persisted_recommendations'] == 1


def test_watchlist_add_list_update_and_delete():
    reset_db()

    create_res = client.post('/api/v1/watchlist', json={'ticker': 'nvda', 'notes': 'AI leader'})
    assert create_res.status_code == 200
    assert create_res.json()['ticker'] == 'NVDA'
    assert create_res.json()['notes'] == 'AI leader'

    update_res = client.post('/api/v1/watchlist', json={'ticker': 'NVDA', 'notes': 'Updated note'})
    assert update_res.status_code == 200
    assert update_res.json()['notes'] == 'Updated note'

    list_res = client.get('/api/v1/watchlist')
    assert list_res.status_code == 200
    assert [item['ticker'] for item in list_res.json()] == ['NVDA']

    delete_res = client.delete('/api/v1/watchlist/NVDA')
    assert delete_res.status_code == 200
    assert delete_res.json() == {'deleted': True, 'ticker': 'NVDA'}

    assert client.get('/api/v1/watchlist').json() == []


def test_watchlist_rejects_invalid_ticker():
    reset_db()

    res = client.post('/api/v1/watchlist', json={'ticker': 'BAD/TICKER', 'notes': ''})

    assert res.status_code == 400
    assert res.json()['error']['message'] == 'Invalid ticker'


def test_missing_watchlist_item_returns_standard_error():
    reset_db()

    res = client.delete('/api/v1/watchlist/NVDA')

    assert res.status_code == 404
    assert res.json()['error']['code'] == 'not_found'
    assert res.json()['error']['message'] == 'Watchlist item not found'


def test_validation_error_returns_standard_error():
    reset_db()

    res = client.get('/api/v1/recommendations/recent?limit=not-a-number')

    assert res.status_code == 422
    assert res.json()['error']['code'] == 'validation_error'
    assert res.json()['error']['details']


def test_openapi_documents_standard_error_schema():
    res = client.get('/openapi.json')

    assert res.status_code == 200
    spec = res.json()
    schemas = spec['components']['schemas']
    assert 'ApiErrorResponse' in schemas
    assert 'ApiErrorBody' in schemas
    top_movers_responses = spec['paths']['/api/v1/market/top-movers']['get']['responses']
    assert '400' in top_movers_responses
    assert '422' in top_movers_responses
    assert '429' in top_movers_responses
    assert '500' in top_movers_responses
    assert '502' in top_movers_responses
    assert top_movers_responses['502']['content']['application/json']['schema']['$ref'].endswith('/ApiErrorResponse')


def test_news_sentiment_returns_default_tracked_tickers():
    reset_db()

    res = client.get('/api/v1/news/sentiment')

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 10
    assert items[0]['ticker'] == 'NVDA'
    assert items[0]['article_count'] >= 1
    assert items[0]['sentiment'] in {'positive', 'neutral', 'negative'}


def test_news_sentiment_filters_tickers_and_deduplicates():
    reset_db()

    res = client.get('/api/v1/news/sentiment?tickers=tsla,nvda,TSLA')

    assert res.status_code == 200
    assert [item['ticker'] for item in res.json()] == ['TSLA', 'NVDA']


def test_news_sentiment_rejects_invalid_ticker():
    reset_db()

    res = client.get('/api/v1/news/sentiment?tickers=NVDA,BAD/TICKER')

    assert res.status_code == 400
