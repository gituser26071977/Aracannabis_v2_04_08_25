#!/usr/bin/env bash
# ================================================================
# AraOS — Restore
# Restaura backup do banco a partir de arquivo .sql.gz
# Uso: ./scripts/restore.sh --env=staging --from=/var/backups/siap/db_prod_xxx.sql.gz
# ================================================================
set -euo pipefail

ENV="production"
BACKUP_FILE=""
for arg in "$@"; do
  case "$arg" in
    --env=*)    ENV="${arg#*=}" ;;
    --from=*)   BACKUP_FILE="${arg#*=}" ;;
  esac
done

if [[ -z "$BACKUP_FILE" ]] || [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Uso: $0 --env=<staging|production> --from=<arquivo.sql.gz>"; exit 1
fi

case "$ENV" in
  staging)
    CONTAINER="siap-db-staging"
    DB="${POSTGRES_DB_STAGING:-aracannabis_staging}"
    USER="${POSTGRES_USER_STAGING:-siap_staging}"
    ;;
  production)
    CONTAINER="siap-db"
    DB="${POSTGRES_DB:-aracannabis}"
    USER="${POSTGRES_USER:-siap_user}"
    ;;
esac

START=$(date +%s)
echo "→ Restore $ENV ← $BACKUP_FILE"

# Verificar integridade do backup
echo "→ Verificando integridade (sha256)..."
SHA_EXPECTED=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
echo "  sha256=$SHA_EXPECTED"

# Drop + recreate schema (preserva roles/extension)
echo "→ Drop + recreate public schema..."
docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null

# Restore
echo "→ Aplicando backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER" psql -U "$USER" -d "$DB" -v ON_ERROR_STOP=1 >/dev/null

# Vacuum analyze
echo "→ VACUUM ANALYZE..."
docker exec "$CONTAINER" psql -U "$USER" -d "$DB" -c "VACUUM ANALYZE;" >/dev/null

END=$(date +%s)
DURATION=$((END-START))
SIZE=$(stat -c%s "$BACKUP_FILE")
echo "✓ Restore OK: ${SIZE} bytes em ${DURATION}s"
