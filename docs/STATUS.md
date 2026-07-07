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

## Next Codex Task
Add Redis-backed provider caching, structured provider logging, and Polygon top market movers integration.

## Working Rules for Codex
After every meaningful change:
1. Update this file
2. Mark completed milestone items in `docs/MILESTONES.md`
3. Add or update tests
4. Do not commit secrets
5. Keep MVP scope tight

## Known Gaps
- Local Docker demo still defaults to mock providers until `POLYGON_API_KEY` is configured
- Polygon top market movers and aggregates are not wired yet
- Watchlist is global/unauthenticated until auth is implemented
- Auth is not implemented
- Polygon provider integration is foundational; production cache/logging/top-movers work remains
- MCP server is documented but not implemented
- Frontend placeholders remain for deeper admin/provider workflows
