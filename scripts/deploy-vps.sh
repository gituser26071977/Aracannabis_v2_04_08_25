#!/usr/bin/env bash
# =============================================================================
# deploy-vps.sh — Script de deploy manual para VPS
# =============================================================================
# Uso: ./scripts/deploy-vps.sh
#
# Idempotente. Faz:
#   1. Backup do banco
#   2. git pull
#   3. docker compose build (sem cache para garantir imagem fresca)
#   4. docker compose up -d (rolling)
#   5. flask db upgrade
#   6. Health checks
#
# Pré-requisitos:
#   - Estar no diretório do projeto (/root/projetos/araos)
#   - Docker + docker compose instalados
#   - Containers atuais: siap-db, siap-backend, siap-frontend, siap-redis, siap-anonymization
#   - .env.production presente
# =============================================================================

set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
DEPLOY_PATH="${DEPLOY_PATH:-/root/projetos/araos}"
BACKUP_DIR="/root/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn()  { echo -e "${YELLOW}[$(date +%H:%M:%S)]${NC} ⚠️  $*"; }
error() { echo -e "${RED}[$(date +%H:%M:%S)]${NC} ❌ $*"; exit 1; }

cd "$DEPLOY_PATH" || error "Diretório $DEPLOY_PATH não acessível"

log "=== [1/8] Backup do banco ==="
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/siap_pre_deploy_${TIMESTAMP}.sql"
if docker exec siap-db pg_dump -U siap_user aracannabis > "$BACKUP_FILE" 2>/dev/null; then
  log "Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
  warn "Backup do banco falhou (db pode estar indisponível). Continuando mesmo assim."
fi

log "=== [2/8] Git pull ==="
git fetch origin main
git stash push -u -m "pre-deploy-stash-${TIMESTAMP}" 2>/dev/null || true
git checkout main
git pull --ff-only origin main
log "Commit atual: $(git log --oneline -1)"

log "=== [3/8] Verificar .env.production ==="
[ -f .env.production ] || error ".env.production não encontrado"

log "=== [4/8] Build das imagens ==="
docker compose -f "$COMPOSE_FILE" build --no-cache siap-backend siap-frontend

log "=== [5/8] Subir DB e Redis ==="
docker compose -f "$COMPOSE_FILE" up -d siap-db siap-redis
for i in {1..10}; do
  if docker exec siap-db pg_isready -U siap_user -d aracannabis >/dev/null 2>&1; then
    log "DB pronto"
    break
  fi
  warn "Aguardando DB... ($i)"
  sleep 3
done

log "=== [6/8] Subir backend ==="
docker compose -f "$COMPOSE_FILE" up -d siap-backend
for i in {1..15}; do
  if docker exec siap-backend curl -fsS http://localhost:5000/api/status >/dev/null 2>&1; then
    log "Backend respondendo"
    break
  fi
  sleep 4
done

log "=== [7/8] Subir frontend e anonymization ==="
docker compose -f "$COMPOSE_FILE" up -d siap-frontend siap-anonymization

log "=== [8/8] Migrations e cleanup ==="
docker exec siap-backend flask db upgrade || warn "Migration falhou (verificar)"

docker image prune -f
docker volume prune -f

log "=== Health checks finais ==="
sleep 10
echo "--- Containers ---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -15
echo
echo "--- Frontend ---"
curl -fsS -o /dev/null -w "HTTP %{http_code} em %{time_total}s\n" https://visualsmartflow.com.br/ || warn "Frontend inacessível"
echo "--- Backend ---"
docker exec siap-backend curl -fsS http://localhost:5000/api/status || warn "Backend não responde"

log "✅ DEPLOY CONCLUÍDO em $TIMESTAMP"
echo
echo "Para rollback:"
echo "  cd $DEPLOY_PATH"
echo "  git log --oneline -5"
echo "  git checkout <commit_anterior>"
echo "  docker compose -f $COMPOSE_FILE up -d --build"
