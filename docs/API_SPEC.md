# API Spec

Base path: `/api/v1`

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
Returns average sentiment and mock news articles by ticker. `tickers` is optional; when omitted, the tracked mega-cap universe is used.

## GET `/admin/status`
Returns app environment, provider modes, provider health, recommendation model, and persisted recommendation count.

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
