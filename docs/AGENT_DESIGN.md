# Agent / MCP Design

## Goal
Expose safe, typed tools that agents can call without directly accessing secrets or databases.

## Initial Tools
- `get_market_overview`
- `get_large_cap_movers`
- `get_ticker_snapshot`
- `get_company_news`
- `analyze_sentiment`
- `generate_recommendation`
- `save_recommendation`
- `explain_recommendation`

## Guardrails
- Read-only market/news tools by default
- No trade execution in MVP
- No financial advice language
- Rate limits
- Audit logs for agent calls
- Tool schemas with strict input validation

## Future MCP Server
Create a separate `mcp-server/` service exposing the above tools. It should call backend service APIs instead of duplicating business logic.
