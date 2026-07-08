# API Spec

Base path: `/api/v1`

## User Context
User-scoped endpoints accept `X-User-Id`. When omitted in local/demo mode, the backend uses `DEFAULT_USER_ID` (`local-demo-user`).

## Error Response
Non-2xx responses use a shared envelope:

```json
{
  "error": {
    "code": "bad_request",
    "message": "Invalid ticker",
    "status_code": 400,
    "request_id": "..."
  }
}
```

Validation errors include an additional `details` array.

FastAPI OpenAPI docs expose this as `ApiErrorResponse` / `ApiErrorBody` and attach common error responses to each route:
- `400` bad request
- `404` resource not found
- `422` validation error
- `429` rate limited
- `500` internal error
- `502` provider error on market/news/provider-backed routes

## GET `/health`
Returns service health.

## GET `/market/overview`
Returns major index summary.

## GET `/market/large-cap-movers?min_market_cap=50000000000`
Returns stocks above market-cap threshold with price movement.

## GET `/market/top-movers?direction=gainers&limit=10`
Returns all-market top gainers or losers from the active provider. `direction` must be `gainers` or `losers`; `limit` is capped at 50.

## GET `/news/sentiment?tickers=NVDA,MSFT`
Returns average sentiment and news articles by ticker, and persists fetched articles for deduped audit history. `tickers` is optional; when omitted, the tracked mega-cap universe is used.

## GET `/news/recent?ticker=NVDA&limit=20`
Returns persisted news article history, newest first. `ticker` is optional and `limit` is capped at 100.

## GET `/admin/status`
Returns app environment, provider modes, provider health, recommendation model, persisted recommendation count, and persisted news article count.

## GET `/agent/tool-contracts`
Returns typed agent/MCP tool contract metadata, including input schema, output envelope schema, safety flags, confirmation requirement, and audit event name.

## GET `/agent/audit-log?tool_name=get_large_cap_movers&limit=20`
Returns recent agent tool audit events. `tool_name` is optional and `limit` is capped at 100.

## POST `/agent/tools/{tool_name}/execute`
Executes a registered agent tool through the contract validator and returns the shared tool envelope.

Body:
- `input`: tool-specific object matching the contract schema
- `confirmed`: required as `true` for write tools such as watchlist updates

## GET `/recommendations/recent?ticker=NVDA&limit=20`
Returns persisted recommendation history, newest first. `ticker` is optional and `limit` is capped at 100.

## GET `/watchlist`
Returns saved watchlist tickers.

## POST `/watchlist`
Creates or updates a watchlist ticker.

Body:
- ticker
- notes

## DELETE `/watchlist/{ticker}`
Removes a ticker from the watchlist.

## GET `/stocks/{ticker}`
Returns ticker snapshot and related news.

## GET `/stocks/{ticker}/candles?days=90`
Returns daily OHLCV candles from the active market provider. `days` is bounded from 20 to 365.

## GET `/stocks/{ticker}/recommendation`
Generates, persists, and returns recommendation object:
- recommendation
- trade_horizon
- confidence_score
- risk_score
- explanation
- supporting_signals
- timestamp
- model_version
- disclaimer

## GET `/stocks/{ticker}/explanation`
Generates a safe fallback narrative for the current recommendation signals without trade execution or financial-advice language.
