#!/usr/bin/env bash
set -euo pipefail

backup_dir="${1:-backups}"
db_user="${POSTGRES_USER:-stock}"
db_name="${POSTGRES_DB:-stock_ai}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_file="${backup_dir}/stock-ai-${timestamp}.dump"

mkdir -p "${backup_dir}"
docker compose exec -T postgres pg_isready -U "${db_user}" -d "${db_name}" >/dev/null
docker compose exec -T postgres pg_dump \
  -U "${db_user}" \
  -d "${db_name}" \
  --format=custom \
  --no-owner \
  --no-acl >"${backup_file}"

checksum="$(shasum -a 256 "${backup_file}" | awk '{print $1}')"
printf '%s  %s\n' "${checksum}" "$(basename "${backup_file}")" >"${backup_file}.sha256"

printf 'Backup: %s\nChecksum: %s\n' "${backup_file}" "${backup_file}.sha256"
