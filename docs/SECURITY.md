# Security

## MVP Controls
- API keys via environment variables only
- No secrets committed
- Ticker input validation
- Backend rate limiting
- CORS allowlist
- Non-root backend Docker user
- SQLAlchemy ORM to reduce SQL injection risk
- CI lint/test workflow

## Production Requirements
- Authentication and authorization
- AWS Secrets Manager or equivalent
- HTTPS only
- Centralized logging with PII/secrets redaction
- Dependency scanning
- Container image scanning
- WAF/rate limiting
- Audit logs for AI agent actions
- Respect API terms, robots.txt, and licensed data restrictions

## Explicit Non-Goals
- No automated trade execution in MVP
- No scraping that violates terms of service
- No secrets in source code
