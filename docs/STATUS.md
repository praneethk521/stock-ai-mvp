# Project Status

## Current State
MVP scaffold created with FastAPI backend, Next.js frontend, Docker Compose, mock providers, and rules-based recommendation engine.

## Last Completed
- Created project structure
- Added backend API routes
- Added mock market/news providers
- Added recommendation engine v1
- Added frontend dashboard, large-cap movers, and stock detail recommendation page
- Added docs and CI skeleton
- Verified local Docker Compose demo with frontend, backend, PostgreSQL, and Redis
- Expanded mock market universe to top-10 mega-cap tickers and ranked movers by absolute daily move
- Added Alembic migration setup and persisted generated recommendations to PostgreSQL
- Added recommendation history API plus Admin and Recommendations UI
- Added watchlist persistence, API endpoints, and Watchlist UI
- Added News Sentiment UI v1 backed by mock provider sentiment summaries
- Added Polygon provider adapter foundation for market snapshots, ticker reference data, and ticker news
- Added Polygon provider health checks, TTL caching, retry/backoff, and RSI/MACD/SMA indicator enrichment
- Added top market movers API/UI, Polygon top movers integration, Redis-backed provider caching, and structured Polygon request logging
- Added historical candle API/provider contract and Polygon aggregate-candle indicator calculations
- Added standardized API error envelope, request IDs, and frontend provider failure states
- Added OpenAPI error response schemas and provider-route response metadata
- Added GitHub Actions CI for backend tests/lint and frontend lint/build
- Added news article persistence, dedupe, recent-news API, and Admin cache visibility
- Added typed MCP/agent tool contract registry with safety metadata
- Added agent tool audit log persistence and contract/audit metadata APIs
- Added agent orchestration service and validated tool execution endpoint
- Added safe fallback AI explanation service and stock explanation API
- Added auth foundation with `X-User-Id` user context and user-scoped watchlists/recommendation history

## Next Codex Task
Add dependency scanning and container scan workflow.

## Working Rules for Codex
After every meaningful change:
1. Update this file
2. Mark completed milestone items in `docs/MILESTONES.md`
3. Add or update tests
4. Do not commit secrets
5. Keep MVP scope tight

## Known Gaps
- Local Docker demo still defaults to mock providers until `POLYGON_API_KEY` is configured
- Auth is header-based foundation only; production identity provider is not implemented
- Polygon plan limits may affect some endpoints; frontend now surfaces provider/API failures with request IDs
- MCP server is documented but not implemented
- Frontend placeholders remain for deeper admin/provider workflows
