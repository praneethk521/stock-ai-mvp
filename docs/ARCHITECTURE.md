# Architecture

## Current Architecture
Next.js frontend calls FastAPI backend. FastAPI uses provider interfaces for market data and news, with mock and Polygon adapters behind configuration. The recommendation engine combines snapshot signals and sentiment into a rules-based recommendation.

## Backend Layers
- API routes: request/response boundaries
- Services: business logic
- Providers: external data source integrations
- Repositories: database access
- Models: SQLAlchemy tables
- Agents: future MCP/agentic tool wrappers

## Data Source Strategy
Use provider interfaces to isolate external APIs from application logic. Mock providers remain available for local development and CI. Polygon is the primary production provider path for market snapshots, reference data, technical indicators, and ticker news. See `DATA_SOURCES.md`.

## Production Hardening Direction
- Validate provider configuration at startup
- Cache provider responses to reduce cost and rate-limit pressure
- Add retry/backoff behavior for transient upstream failures
- Add structured logs with provider request IDs
- Add provider health checks surfaced in Admin
- Add auth before user-specific watchlists or saved preferences

## Deployment Direction
- Local: Docker Compose
- Production: AWS ECS/Fargate or EKS
- Database: RDS PostgreSQL
- Cache/Queue: ElastiCache Redis
- Secrets: AWS Secrets Manager
