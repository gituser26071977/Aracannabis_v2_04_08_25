#!/usr/bin/env bash
# ================================================================
# AraOS — Rollback
# Reverte para o backup mais recente pré-deploy
# Uso: ./scripts/rollback.sh [--env=staging|production] [--to-backup=FILE]
# ================================================================
set -euo pipefail

ENV="production"
BACKUP_FILE=""
for arg in "$@"; do
  case "$arg" in
    --env=*)      ENV="${arg#*=}" ;;
    --to-backup=*) BACKUP_FILE="${arg#*=}" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

case "$ENV" in
  staging)
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.staging.yml"
    ENV_FILE="$PROJECT_ROOT/.env.staging"
    BACKUP_DIR="/var/backups/siap-staging"
    ;;
  production)
    COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
    ENV_FILE="$PROJECT_ROOT/.env.production"
    BACKUP_DIR="/var/backups/siap"
    ;;
  *) echo "ENV inválida: $ENV"; exit 1 ;;
esac

START=$(date +%s)
echo "════════════════════════════════════════"
echo "  AraOS — ROLLBACK ($ENV)"
echo "  $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════════"

# 1. Encontrar backup mais recente se não especificado
if [[ -z "$BACKUP_FILE" ]]; then
  BACKUP_FILE=$(ls -t "$BACKUP_DIR"/db_*.sql.gz 2>/dev/null | head -1 || echo "")
  if [[ -z "$BACKUP_FILE" ]]; then echo "✗ Nenhum backup encontrado em $BACKUP_DIR"; exit 1; fi
fi
echo "→ Backup alvo: $BACKUP_FILE"

# 2. Stop backend (libera conexões PG)
echo "→ Stop backend..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop siap-backend

# 3. Restore DB
echo "→ Restaurando banco..."
"$SCRIPT_DIR/restore.sh" --env="$ENV" --from="$BACKUP_FILE"

# 4. Start backend
echo "→ Start backend..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d siap-backend

# 5. Smoke pós-rollback
"$SCRIPT_DIR/smoke.sh" --env="$ENV" || { echo "✗ Smoke pós-rollback falhou"; exit 1; }

END=$(date +%s)
echo "════════════════════════════════════════"
echo "  ✓ Rollback concluído em $((END-START))s"
echo "════════════════════════════════════════"
