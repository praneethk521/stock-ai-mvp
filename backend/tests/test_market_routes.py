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


def test_stock_recommendation_accepts_class_share_ticker():
    reset_db()
    res = client.get('/api/v1/stocks/BRK.B/recommendation')

    assert res.status_code == 200
    assert res.json()['ticker'] == 'BRK.B'

    with TestingSessionLocal() as db:
        saved = db.query(RecommendationRecord).filter_by(ticker='BRK.B').one()
        assert saved.recommendation == res.json()['recommendation']


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
