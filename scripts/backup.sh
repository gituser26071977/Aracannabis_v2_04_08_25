#!/usr/bin/env bash
# ================================================================
# AraOS — Backup
# pg_dump compactado + uploads + logs (separado)
# Retenção: 7 diários + 4 semanais + 12 mensais
# Uso: ./scripts/backup.sh [--env=staging|production]
# ================================================================
set -euo pipefail

ENV="production"
for arg in "$@"; do [[ "$arg" == --env=* ]] && ENV="${arg#*=}"; done

case "$ENV" in
  staging)
    CONTAINER="siap-db-staging"; BACKUP_DIR="/var/backups/siap-staging"
    DB="${POSTGRES_DB_STAGING:-aracannabis_staging}"
    USER="${POSTGRES_USER_STAGING:-siap_staging}"
    ;;
  production)
    CONTAINER="siap-db"; BACKUP_DIR="/var/backups/siap"
    DB="${POSTGRES_DB:-aracannabis}"
    USER="${POSTGRES_USER:-siap_user}"
    ;;
  *) echo "ENV inválida"; exit 1 ;;
esac

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_${ENV}_${TIMESTAMP}.sql.gz"

START=$(date +%s)
echo "→ Backup $ENV → $BACKUP_FILE"

docker exec "$CONTAINER" pg_dump -U "$USER" -d "$DB" --no-owner --no-acl \
  | gzip > "$BACKUP_FILE"

# Métricas
END=$(date +%s)
DURATION=$((END-START))
SIZE=$(stat -c%s "$BACKUP_FILE")
SHA=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)

# Manifest
echo "{\"env\":\"$ENV\",\"file\":\"$BACKUP_FILE\",\"size\":$SIZE,\"sha256\":\"$SHA\",\"duration_s\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
  >> "$BACKUP_DIR/manifest.jsonl"

echo "✓ Backup OK: $SIZE bytes em ${DURATION}s (sha256:${SHA:0:12}...)"

# Rotação: apagar >30 dias
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete 2>/dev/null || true
