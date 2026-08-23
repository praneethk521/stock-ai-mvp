# Backup and Restore

PostgreSQL is the system of record. Redis contains disposable cache data and is rebuilt after recovery. API keys and identity-provider secrets must be restored through the runtime secret manager, not from database backups.

## Recovery Targets

Initial production targets are a recovery point objective of 15 minutes and a recovery time objective of 60 minutes. These are engineering targets until a staging restore drill demonstrates them and product owners approve them.

Production PostgreSQL should use encrypted automated backups, point-in-time recovery, cross-zone durability, and a retention period of at least 14 days. Keep one monthly snapshot for 12 months only if the data retention policy permits it.

## Local Backup

With the Compose database running:

```bash
./scripts/backup-local-db.sh
```

The script writes a PostgreSQL custom-format archive and SHA-256 checksum under the ignored `backups/` directory. An alternate output directory may be passed as its first argument.

## Local Restore Drill

Restore replaces the local `stock_ai` database. The script validates the archive and checksum before stopping the backend, and it requires an explicit confirmation value:

```bash
CONFIRM_RESTORE=stock_ai ./scripts/restore-local-db.sh backups/stock-ai-YYYYMMDDTHHMMSSZ.dump
```

After the restore, the script applies forward-compatible Alembic migrations and restarts the backend. Verify liveness, readiness, watchlist data, recommendation history, and recent news records.

## Production Recovery

1. Declare the incident, record the suspected data-loss window, and pause application writes or scale the backend to zero.
2. Select a restore point before the corruption or outage. Preserve the damaged database for investigation.
3. Restore the managed PostgreSQL backup into a new isolated database instance. Never overwrite the only copy in place.
4. Run integrity checks, record counts, and application smoke tests against the isolated restore.
5. Run `alembic current` and `alembic upgrade head` with the exact backend image intended for recovery.
6. Rotate database credentials, update the runtime secret reference, and deploy the backend against the restored instance.
7. Verify `/api/v1/health/ready`, authenticated user data, provider connectivity, and error/latency metrics before reopening traffic.
8. Rebuild Redis rather than restoring stale cache data. Monitor cache warm-up and provider rate limits.
9. Record achieved RPO/RTO, affected users, validation evidence, and follow-up actions.

## Scheduled Validation

Run a staging restore drill at least quarterly and after material schema or backup-policy changes. A successful drill must verify archive readability, migration compatibility, representative user records, checksums, and measured recovery time. Backup existence alone is not recovery evidence.
