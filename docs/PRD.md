# Product Requirements Document

## Product Vision
Build a secure, production-grade stock insights application that combines market data, large-cap movers, news sentiment, technical indicators, and AI-assisted recommendations.

## Users
- Retail investor researching stocks
- Active trader looking for intraday/weekly ideas
- Admin/operator monitoring data pipelines and model outputs

## Delivered Product Scope
1. Dashboard with market overview
2. Large-cap movers with market cap filter, default $50B+
3. Stock detail page
4. News sentiment with persisted provider articles
5. Rules-based recommendation v1
6. Visible financial disclaimer
7. Persisted, user-scoped watchlists and recommendation history
8. Polygon market/news provider with caching, retries, and technical indicators
9. Agent tool contracts, execution audit records, and safe explanation fallback
10. Local Docker Compose and portable Kubernetes deployment paths

## Remaining Product Scope
- Production identity provider provisioning and frontend sign-in/session flow
- Alerts
- Backtesting
- LLM-backed explanations with evaluation and safety gates
- Model training pipeline
- MCP server integration
- Production cloud environment and release automation
- Operational dashboards, alerting, backup, and recovery validation

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
- Scope watchlists and recommendation history by user context
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
- Health probes, horizontal scaling, and controlled database migrations
- Dependency and container vulnerability scanning

## Acceptance Criteria
- App runs locally with Docker Compose
- Backend exposes health, market overview, large-cap movers, stock details, and recommendation endpoints
- Frontend renders dashboard, large-cap movers, and stock recommendation page
- Docs clearly define next milestones
- Recommendation includes disclaimer
- Production containers run non-root processes and use runtime configuration
- Kubernetes manifests render successfully and separate migrations from API startup
