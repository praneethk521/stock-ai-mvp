import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.tools import get_large_cap_movers_tool
from app.core.db import Base, get_db
from app.main import app
from app.models.agent import AgentToolAuditLog
from app.models.news import NewsArticleRecord
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


def test_stock_explanation_returns_safe_fallback_narrative():
    reset_db()

    res = client.get('/api/v1/stocks/NVDA/explanation')

    assert res.status_code == 200
    data = res.json()
    assert data['ticker'] == 'NVDA'
    assert data['provider'] == 'rules-fallback'
    assert data['model_version'] == 'explanation-fallback-v1'
    assert data['signal_summary']
    assert data['risk_notes']
    assert data['disclaimer'] == 'Informational only. Not financial advice.'


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
    assert data['persisted_news_articles'] == 2


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


def test_agent_tool_contracts_endpoint_returns_contract_metadata():
    reset_db()

    res = client.get('/api/v1/agent/tool-contracts')

    assert res.status_code == 200
    contracts = res.json()
    names = {item['name'] for item in contracts}
    assert 'get_large_cap_movers' in names
    assert 'generate_recommendation' in names
    assert all(item['audit_event'].startswith('agent.tool.') for item in contracts)


def test_agent_audit_log_endpoint_returns_recent_events():
    reset_db()
    with TestingSessionLocal() as db:
        db.add(
            AgentToolAuditLog(
                tool_name='get_large_cap_movers',
                audit_event='agent.tool.get_large_cap_movers',
                ok=True,
                input_payload={'min_market_cap': 50_000_000_000},
                output_summary={'item_count': 10},
                duration_ms=5,
            )
        )
        db.commit()

    res = client.get('/api/v1/agent/audit-log')

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]['tool_name'] == 'get_large_cap_movers'
    assert items[0]['ok'] is True


def test_agent_tool_execute_runs_registered_tool_and_audits():
    reset_db()

    res = client.post('/api/v1/agent/tools/get_large_cap_movers/execute', json={'input': {'min_market_cap': 50_000_000_000}})

    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert len(data['data']['items']) == 10

    audit_res = client.get('/api/v1/agent/audit-log?tool_name=get_large_cap_movers')
    assert audit_res.status_code == 200
    audit = audit_res.json()[0]
    assert audit['ok'] is True
    assert audit['output_summary'] == {'item_count': 10}


def test_agent_tool_execute_requires_confirmation_for_write_tools():
    reset_db()

    res = client.post('/api/v1/agent/tools/upsert_watchlist_item/execute', json={'input': {'ticker': 'NVDA', 'notes': 'AI'}})

    assert res.status_code == 200
    body = res.json()
    assert body['ok'] is False
    assert body['error']['code'] == 'confirmation_required'


def test_agent_tool_execute_confirmed_write_tool_updates_watchlist():
    reset_db()

    res = client.post(
        '/api/v1/agent/tools/upsert_watchlist_item/execute',
        json={'input': {'ticker': 'NVDA', 'notes': 'AI leader'}, 'confirmed': True},
    )

    assert res.status_code == 200
    body = res.json()
    assert body['ok'] is True
    assert body['data']['ticker'] == 'NVDA'
    assert client.get('/api/v1/watchlist').json()[0]['notes'] == 'AI leader'


@pytest.mark.asyncio
async def test_agent_tool_wrapper_records_audit_log():
    reset_db()
    with TestingSessionLocal() as db:
        result = await get_large_cap_movers_tool(db=db)

    assert len(result['items']) == 10
    with TestingSessionLocal() as db:
        audit = db.query(AgentToolAuditLog).one()
        assert audit.tool_name == 'get_large_cap_movers'
        assert audit.ok is True
        assert audit.output_summary == {'item_count': 10}


def test_news_sentiment_returns_default_tracked_tickers():
    reset_db()

    res = client.get('/api/v1/news/sentiment')

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 10
    assert items[0]['ticker'] == 'NVDA'
    assert items[0]['article_count'] >= 1
    assert items[0]['sentiment'] in {'positive', 'neutral', 'negative'}

    with TestingSessionLocal() as db:
        assert db.query(NewsArticleRecord).count() >= 10


def test_news_sentiment_filters_tickers_and_deduplicates():
    reset_db()

    res = client.get('/api/v1/news/sentiment?tickers=tsla,nvda,TSLA')

    assert res.status_code == 200
    assert [item['ticker'] for item in res.json()] == ['TSLA', 'NVDA']

    repeat_res = client.get('/api/v1/news/sentiment?tickers=TSLA,NVDA')
    assert repeat_res.status_code == 200

    with TestingSessionLocal() as db:
        assert db.query(NewsArticleRecord).count() == 4


def test_recent_news_returns_persisted_articles():
    reset_db()
    client.get('/api/v1/news/sentiment?tickers=NVDA,TSLA')

    res = client.get('/api/v1/news/recent?ticker=NVDA&limit=10')

    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    assert {item['ticker'] for item in items} == {'NVDA'}
    assert all(item['provider'] == 'mock' for item in items)
    assert all(item['first_seen_at'] for item in items)
    assert all(item['last_seen_at'] for item in items)


def test_news_sentiment_rejects_invalid_ticker():
    reset_db()

    res = client.get('/api/v1/news/sentiment?tickers=NVDA,BAD/TICKER')

    assert res.status_code == 400
