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

## Next Codex Task
Add watchlist persistence and build the Watchlist UI.

## Working Rules for Codex
After every meaningful change:
1. Update this file
2. Mark completed milestone items in `docs/MILESTONES.md`
3. Add or update tests
4. Do not commit secrets
5. Keep MVP scope tight

## Known Gaps
- Data is mocked
- Top-10 market cap list is an illustrative mock universe and should be replaced by a real market-data provider
- Watchlist UI is still a placeholder
- Auth is not implemented
- Real provider integrations are not implemented
- MCP server is documented but not implemented
- Frontend placeholders remain for several tabs
