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


def test_large_cap_movers_returns_top_ten_sorted_by_absolute_move():
    res = client.get('/api/v1/market/large-cap-movers')

    assert res.status_code == 200
    items = res.json()['items']
    assert len(items) == 10
    assert items[0]['ticker'] == 'TSLA'
    assert abs(items[0]['change_percent']) >= abs(items[-1]['change_percent'])


def test_stock_recommendation_accepts_class_share_ticker():
    res = client.get('/api/v1/stocks/BRK.B/recommendation')

    assert res.status_code == 200
    assert res.json()['ticker'] == 'BRK.B'

    with TestingSessionLocal() as db:
        saved = db.query(RecommendationRecord).filter_by(ticker='BRK.B').one()
        assert saved.recommendation == res.json()['recommendation']
