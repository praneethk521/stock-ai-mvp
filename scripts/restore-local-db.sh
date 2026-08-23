#!/usr/bin/env bash
set -euo pipefail

backup_file="${1:-}"
db_user="${POSTGRES_USER:-stock}"
db_name="${POSTGRES_DB:-stock_ai}"

if [[ -z "${backup_file}" || ! -f "${backup_file}" ]]; then
  printf 'Usage: CONFIRM_RESTORE=stock_ai %s /path/to/backup.dump\n' "$0" >&2
  exit 2
fi

if [[ "${CONFIRM_RESTORE:-}" != "${db_name}" ]]; then
  printf 'Refusing restore. Set CONFIRM_RESTORE=%s to replace the local database.\n' "${db_name}" >&2
  exit 2
fi

if [[ -f "${backup_file}.sha256" ]]; then
  expected_checksum="$(awk '{print $1}' "${backup_file}.sha256")"
  actual_checksum="$(shasum -a 256 "${backup_file}" | awk '{print $1}')"
  if [[ "${actual_checksum}" != "${expected_checksum}" ]]; then
    printf 'Backup checksum verification failed.\n' >&2
    exit 1
  fi
fi

docker compose exec -T postgres pg_restore --list <"${backup_file}" >/dev/null
docker compose stop backend
docker compose exec -T postgres dropdb --if-exists -U "${db_user}" "${db_name}"
docker compose exec -T postgres createdb -U "${db_user}" "${db_name}"
docker compose exec -T postgres pg_restore \
  -U "${db_user}" \
  -d "${db_name}" \
  --exit-on-error \
  --no-owner \
  --no-acl <"${backup_file}"
docker compose run --rm backend alembic upgrade head
docker compose up -d backend

printf 'Restored %s from %s\n' "${db_name}" "${backup_file}"
