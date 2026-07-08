# Product Requirements Document

## Product Vision
Build a secure, production-grade stock insights application that combines market data, large-cap movers, news sentiment, technical indicators, and AI-assisted recommendations.

## Users
- Retail investor researching stocks
- Active trader looking for intraday/weekly ideas
- Admin/operator monitoring data pipelines and model outputs

## MVP Features
1. Dashboard with market overview
2. Large-cap movers with market cap filter, default $50B+
3. Stock detail page
4. News sentiment placeholder/provider interface
5. Rules-based recommendation v1
6. Visible financial disclaimer
7. Extensible provider and agent/tool architecture

## Future Scope
- Real market data providers: Polygon, Finnhub, Alpha Vantage, Tiingo, IEX-style providers
- Authenticated user watchlists
- Alerts
- Backtesting
- Recommendation history
- LLM explanations
- Model training pipeline
- MCP server integration
- Kubernetes deployment

## Functional Requirements
- Fetch market overview
- Fetch large-cap movers
- Fetch stock snapshot
- Fetch historical OHLCV candles
- Fetch news by ticker
- Persist and deduplicate provider news articles for auditability
- Score sentiment
- Calculate technical indicators from historical candles
- Generate BUY/SELL/HOLD/WATCH recommendation
- Generate safe recommendation explanation narratives
- Return confidence, risk, explanation, supporting signals, timestamp, model version

## Non-Functional Requirements
- Secure API key handling
- No secrets in code
- Validated inputs
- Rate limiting
- Structured logs
- Tests and CI
- Provider abstraction
- Safe scraping/API compliance

## Acceptance Criteria
- App runs locally with Docker Compose
- Backend exposes health, market overview, large-cap movers, stock details, and recommendation endpoints
- Frontend renders dashboard, large-cap movers, and stock recommendation page
- Docs clearly define next milestones
- Recommendation includes disclaimer
