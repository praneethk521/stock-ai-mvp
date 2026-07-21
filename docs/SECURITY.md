# Security

## MVP Controls
- API keys via environment variables only
- Optional file-mounted secret adapter for production runtimes
- No secrets committed
- Ticker input validation
- Backend rate limiting
- CORS allowlist
- Non-root backend Docker user
- SQLAlchemy ORM to reduce SQL injection risk
- CI lint/test workflow
- GitHub Actions dependency scan with pip-audit and pnpm audit
- GitHub Actions container image scan with Trivy for backend and frontend images
- User-scoped watchlist and recommendation history access through request user context
- Agent tool execution audit logs

## Production Requirements
- Authentication and authorization
- AWS Secrets Manager or equivalent, mounted or injected through the runtime secret adapter
- HTTPS only
- Centralized logging with PII/secrets redaction
- Dependency scanning with release/PR gates
- Container image scanning with release/PR gates
- WAF/rate limiting
- Audit logs for AI agent actions
- Respect API terms, robots.txt, and licensed data restrictions

## Security Automation
- `.github/workflows/security.yml` runs backend dependency audits with `pip-audit`.
- The same workflow runs frontend dependency audits with `pnpm audit --audit-level high`.
- Backend and frontend Docker images are built and scanned with Trivy for high/critical OS and library vulnerabilities.
- The workflow also runs weekly so new advisories are detected even when application code does not change.

## Runtime Secrets
- Local demos use `SECRET_PROVIDER=env` and read values such as `POLYGON_API_KEY` from `.env` or process environment.
- Production runtimes can use `SECRET_PROVIDER=file` with `SECRETS_DIR=/run/secrets`.
- Secret filenames are configured with fields such as `POLYGON_API_KEY_SECRET_NAME`; direct environment values still take precedence for local overrides.
- Admin status reports only the selected `secret_provider`, never secret values.

## Explicit Non-Goals
- No automated trade execution in MVP
- No scraping that violates terms of service
- No secrets in source code
