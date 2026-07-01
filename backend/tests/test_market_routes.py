from fastapi.testclient import TestClient

from app.main import app


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
