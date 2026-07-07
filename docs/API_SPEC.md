# API Spec

Base path: `/api/v1`

## GET `/health`
Returns service health.

## GET `/market/overview`
Returns major index summary.

## GET `/market/large-cap-movers?min_market_cap=50000000000`
Returns stocks above market-cap threshold with price movement.

## GET `/admin/status`
Returns app environment, provider modes, recommendation model, and persisted recommendation count.

## GET `/recommendations/recent?ticker=NVDA&limit=20`
Returns persisted recommendation history, newest first. `ticker` is optional and `limit` is capped at 100.

## GET `/stocks/{ticker}`
Returns ticker snapshot and related news.

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
