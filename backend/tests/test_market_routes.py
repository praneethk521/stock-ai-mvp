import json

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.tools import get_large_cap_movers_tool
from app.core.config import get_settings
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


def test_liveness_and_readiness_health_checks():
    reset_db()

    live_res = client.get('/api/v1/health/live')
    ready_res = client.get('/api/v1/health/ready')

    assert live_res.status_code == 200
    assert live_res.json() == {'status': 'alive'}
    assert ready_res.status_code == 200
    assert ready_res.json() == {'status': 'ready', 'checks': {'database': 'ok'}}


def test_metrics_expose_http_request_counters_and_request_id():
    reset_db()

    health_res = client.get('/api/v1/health/live', headers={'x-request-id': 'test-request-id'})
    client.get('/api/v1/stocks/NVDA/recommendation')
    metrics_res = client.get('/metrics')

    assert health_res.headers['x-request-id'] == 'test-request-id'
    assert metrics_res.status_code == 200
    assert metrics_res.headers['content-type'].startswith('text/plain')
    assert 'stock_ai_http_requests_total' in metrics_res.text
    assert 'route="/api/v1/health/live"' in metrics_res.text
    assert 'route="/api/v1/stocks/{ticker}/recommendation"' in metrics_res.text
    assert 'route="/api/v1/stocks/NVDA/recommendation"' not in metrics_res.text


def test_request_completion_log_has_correlation_fields(capsys: pytest.CaptureFixture[str]):
    client.get('/api/v1/health/live', headers={'x-request-id': 'structured-log-test'})

    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    request_event = next(event for event in events if event.get('request_id') == 'structured-log-test')

    assert request_event['event'] == 'request_completed'
    assert request_event['route'] == '/api/v1/health/live'
    assert request_event['status_code'] == 200
    assert request_event['duration_ms'] >= 0
    assert {'timestamp', 'level', 'method', 'trace_id', 'span_id'} <= request_event.keys()


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


def test_recent_recommendations_are_user_scoped():
    reset_db()
    client.get('/api/v1/stocks/NVDA/recommendation', headers={'x-user-id': 'user-a'})
    client.get('/api/v1/stocks/TSLA/recommendation', headers={'x-user-id': 'user-b'})

    user_a = client.get('/api/v1/recommendations/recent', headers={'x-user-id': 'user-a'})
    user_b = client.get('/api/v1/recommendations/recent', headers={'x-user-id': 'user-b'})

    assert [item['ticker'] for item in user_a.json()] == ['NVDA']
    assert [item['ticker'] for item in user_b.json()] == ['TSLA']


def test_admin_status_includes_persistence_count():
    reset_db()
    client.get('/api/v1/stocks/NVDA/recommendation')

    res = client.get('/api/v1/admin/status')

    assert res.status_code == 200
    data = res.json()
    assert data['market_data_provider'] == 'mock'
    assert data['auth_mode'] == 'local'
    assert data['secret_provider'] == 'env'
    assert data['metrics_enabled'] is True
    assert data['tracing_enabled'] is False
    assert data['otel_service_name'] == 'stock-ai-backend'
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


def test_watchlist_is_user_scoped():
    reset_db()

    client.post('/api/v1/watchlist', json={'ticker': 'NVDA', 'notes': 'User A'}, headers={'x-user-id': 'user-a'})
    client.post('/api/v1/watchlist', json={'ticker': 'TSLA', 'notes': 'User B'}, headers={'x-user-id': 'user-b'})

    user_a = client.get('/api/v1/watchlist', headers={'x-user-id': 'user-a'})
    user_b = client.get('/api/v1/watchlist', headers={'x-user-id': 'user-b'})

    assert [item['ticker'] for item in user_a.json()] == ['NVDA']
    assert [item['ticker'] for item in user_b.json()] == ['TSLA']


def test_price_alert_crud_is_user_scoped():
    reset_db()
    headers = {'x-user-id': 'alert-user'}

    create_res = client.post(
        '/api/v1/alerts',
        json={'ticker': 'nvda', 'condition': 'above', 'target_price': 210},
        headers=headers,
    )
    assert create_res.status_code == 201
    alert = create_res.json()
    assert alert['ticker'] == 'NVDA'
    assert alert['is_active'] is True

    assert client.get('/api/v1/alerts', headers={'x-user-id': 'other-user'}).json() == []
    unauthorized_delete = client.delete(f"/api/v1/alerts/{alert['id']}", headers={'x-user-id': 'other-user'})
    assert unauthorized_delete.status_code == 404

    update_res = client.put(
        f"/api/v1/alerts/{alert['id']}",
        json={'target_price': 205, 'is_active': True},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()['target_price'] == 205

    delete_res = client.delete(f"/api/v1/alerts/{alert['id']}", headers=headers)
    assert delete_res.json() == {'deleted': True, 'id': alert['id']}


def test_price_alert_evaluation_triggers_met_threshold_once():
    reset_db()
    headers = {'x-user-id': 'alert-user'}
    above = client.post(
        '/api/v1/alerts',
        json={'ticker': 'NVDA', 'condition': 'above', 'target_price': 190},
        headers=headers,
    ).json()
    below = client.post(
        '/api/v1/alerts',
        json={'ticker': 'NVDA', 'condition': 'below', 'target_price': 190},
        headers=headers,
    ).json()

    evaluate_res = client.post('/api/v1/alerts/evaluate', headers=headers)

    assert evaluate_res.status_code == 200
    evaluated = {item['id']: item for item in evaluate_res.json()}
    assert evaluated[above['id']]['is_active'] is False
    assert evaluated[above['id']]['triggered_at'] is not None
    assert evaluated[above['id']]['last_price'] == 200.09
    assert evaluated[below['id']]['is_active'] is True
    assert evaluated[below['id']]['triggered_at'] is None

    active = client.get('/api/v1/alerts?active_only=true', headers=headers).json()
    assert [item['id'] for item in active] == [below['id']]


def test_price_alert_rejects_invalid_threshold():
    reset_db()

    res = client.post(
        '/api/v1/alerts',
        json={'ticker': 'NVDA', 'condition': 'above', 'target_price': 0},
    )

    assert res.status_code == 422


def test_jwt_auth_mode_requires_bearer_token(monkeypatch: pytest.MonkeyPatch):
    reset_db()
    jwt_secret = 'test-secret-with-at-least-32-bytes'
    monkeypatch.setenv('AUTH_MODE', 'jwt')
    monkeypatch.setenv('AUTH_JWT_ALGORITHM', 'HS256')
    monkeypatch.setenv('AUTH_JWT_SECRET', jwt_secret)
    get_settings.cache_clear()

    try:
        res = client.get('/api/v1/watchlist')
    finally:
        get_settings.cache_clear()

    assert res.status_code == 401
    assert res.json()['error']['message'] == 'Missing bearer token'


def test_jwt_auth_mode_uses_token_subject_for_user_scope(monkeypatch: pytest.MonkeyPatch):
    reset_db()
    jwt_secret = 'test-secret-with-at-least-32-bytes'
    monkeypatch.setenv('AUTH_MODE', 'jwt')
    monkeypatch.setenv('AUTH_JWT_ALGORITHM', 'HS256')
    monkeypatch.setenv('AUTH_JWT_SECRET', jwt_secret)
    get_settings.cache_clear()
    token = jwt.encode({'sub': 'jwt-user'}, jwt_secret, algorithm='HS256')

    try:
        create_res = client.post(
            '/api/v1/watchlist',
            json={'ticker': 'NVDA', 'notes': 'JWT scoped'},
            headers={'authorization': f'Bearer {token}'},
        )
        list_res = client.get('/api/v1/watchlist', headers={'authorization': f'Bearer {token}'})
    finally:
        get_settings.cache_clear()

    assert create_res.status_code == 200
    assert [item['ticker'] for item in list_res.json()] == ['NVDA']


def test_rejects_invalid_user_id_header():
    reset_db()

    res = client.get('/api/v1/watchlist', headers={'x-user-id': 'bad/user'})

    assert res.status_code == 400
    assert res.json()['error']['message'] == 'Invalid user id'


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
    assert 'PriceAlertCreate' in schemas
    assert 'PriceAlertRead' in schemas
    assert 'PriceAlertUpdate' in schemas
    assert {'get', 'post'} <= spec['paths']['/api/v1/alerts'].keys()
    assert {'put', 'delete'} <= spec['paths']['/api/v1/alerts/{alert_id}'].keys()
    assert 'post' in spec['paths']['/api/v1/alerts/evaluate']
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
