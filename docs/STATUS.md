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

## Next Codex Task
Implement Alembic migrations and persist generated recommendations to PostgreSQL.

## Working Rules for Codex
After every meaningful change:
1. Update this file
2. Mark completed milestone items in `docs/MILESTONES.md`
3. Add or update tests
4. Do not commit secrets
5. Keep MVP scope tight

## Known Gaps
- Data is mocked
- Auth is not implemented
- Real provider integrations are not implemented
- MCP server is documented but not implemented
- Frontend placeholders remain for several tabs
