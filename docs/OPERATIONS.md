# Operations Runbook

## Signal Ownership

Prometheus rule definitions live in `infra/observability/prometheus-rules.yaml`. They require application metrics plus `kube-state-metrics` for Kubernetes workload alerts. Route notifications through the deployment platform's Alertmanager integration, and replace repository-relative `runbook` annotations with the deployed documentation URL.

Container JSON logs are the centralized logging contract. Ship standard output with the platform collector and parse request completion events against `infra/observability/request-log.schema.json`. Retain `request_id`, `trace_id`, `route`, `status_code`, and `duration_ms` as indexed fields. Do not index raw URLs, authorization headers, API keys, request bodies, or user-provided notes.

## Backend High Error Rate

1. Correlate the alert window with deploys, migration jobs, and provider health in `/api/v1/admin/status`.
2. Group request logs by templated route and request ID; inspect linked traces when enabled.
3. Check PostgreSQL, Redis, Polygon rate limits, and secret availability.
4. Roll back the application image if errors began after a release and migrations remain backward compatible.
5. Escalate if the error ratio remains above 5% after mitigation.

## Backend High Latency

1. Identify slow templated routes and compare provider timing, database saturation, cache hit behavior, and pod CPU.
2. Confirm horizontal scaling is active and ready replicas are receiving traffic.
3. Reduce provider pressure or disable a degraded optional integration through configuration when possible.
4. Escalate if p95 latency remains above 1.5 seconds for user-facing requests.

## Backend Metrics Missing

1. Check backend pod readiness and direct service access to `/metrics` from the Prometheus namespace.
2. Verify scrape annotations, network policy, and `METRICS_ENABLED` configuration.
3. Check Prometheus target discovery and ingestion health before restarting the application.

## Deployment Unavailable

1. Inspect deployment conditions, pending pods, events, health probes, and resource quotas.
2. Confirm image pull access and runtime Secret/ConfigMap availability.
3. Preserve logs from terminating pods and roll back a failing image when appropriate.

## Container Restarting

1. Inspect current and previous container logs and pod termination reason.
2. Check memory limits, health probe failures, missing configuration, and dependency connectivity.
3. Avoid increasing restart thresholds to hide a repeatable application failure.

## Migration Failed

1. Keep the application rollout blocked and preserve the failed job logs.
2. Verify the database target, credentials, current Alembic revision, and exact release image.
3. Restore from a verified backup if the migration partially changed data and is not safely resumable.
4. Correct or supersede the migration, validate it on a restored staging copy, then rerun with a unique job name.

## Incident Closeout

Record timeline, customer impact, request/trace IDs, root cause, recovery action, and prevention work. Tune alert thresholds only from measured staging or production behavior. Database recovery procedures are in `docs/BACKUP_RESTORE.md`.
