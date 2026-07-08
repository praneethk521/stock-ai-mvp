# Agent / MCP Design

## Goal
Expose safe, typed tools that agents can call without directly accessing secrets or databases.

## Contract Registry
Typed tool contracts live in `backend/app/agents/contracts.py`. Each contract defines:
- tool name
- description
- JSON input schema
- JSON output envelope schema
- read/write safety classification
- confirmation requirement
- audit event name

## Initial Tools
- `get_market_overview`
- `get_large_cap_movers`
- `get_top_market_movers`
- `get_ticker_snapshot`
- `get_historical_candles`
- `get_company_news`
- `get_recent_news`
- `generate_recommendation`
- `list_recent_recommendations`
- `list_watchlist`
- `upsert_watchlist_item`
- `delete_watchlist_item`

## Guardrails
- Read-only market/news tools by default
- Watchlist write tools require confirmation
- No trade execution in MVP
- No financial advice language
- Rate limits
- Audit logs for agent calls in `agent_tool_audit_logs`
- Tool schemas with strict input validation

## Backend Integration
- `GET /api/v1/agent/tool-contracts` exposes contract metadata for a future MCP server.
- `GET /api/v1/agent/audit-log` exposes recent tool audit events for operators.
- `POST /api/v1/agent/tools/{tool_name}/execute` validates and executes registered tools through the orchestration service.
- Existing Python tool wrappers can record audit events when invoked with a database session.

## Future MCP Server
Create a separate `mcp-server/` service exposing the above contracts. It should call backend service APIs instead of duplicating business logic, wrap responses in the shared tool envelope, and emit audit events named by each contract.
