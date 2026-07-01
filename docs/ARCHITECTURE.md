# Architecture

## MVP Architecture
Next.js frontend calls FastAPI backend. FastAPI uses provider interfaces for market data and news. The recommendation engine combines snapshot signals and sentiment into a rules-based recommendation.

## Backend Layers
- API routes: request/response boundaries
- Services: business logic
- Providers: external data source integrations
- Repositories: database access
- Models: SQLAlchemy tables
- Agents: future MCP/agentic tool wrappers

## Data Source Strategy
Use provider interfaces to avoid locking into one API. Start with mock data, then implement Polygon/Finnhub/Alpha Vantage adapters.

Polygon provides real-time and historical market data APIs. Finnhub offers real-time market data, company fundamentals, news, and sentiment-related datasets. Alpha Vantage offers stock APIs and a market news/sentiment endpoint, and also advertises an MCP server for agentic workflows. See `DATA_SOURCES.md`.

## Deployment Direction
- Local: Docker Compose
- Production: AWS ECS/Fargate or EKS
- Database: RDS PostgreSQL
- Cache/Queue: ElastiCache Redis
- Secrets: AWS Secrets Manager
