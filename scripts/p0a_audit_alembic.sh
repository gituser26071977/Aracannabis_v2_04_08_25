#!/bin/bash
# scripts/p0a_audit_alembic.sh
#
# P0-A FASE 2 — Auditoria do estado Alembic em PRODUCAO
#
# Coleta:
#   - SELECT version_num FROM alembic_version  (qual migration esta aplicada)
#   - flask db heads                          (heads detectadas pelo Alembic)
#   - flask db current                        (qual revisao o banco esta)
#   - divergencias entre revisao atual e cadeia
#
# NAO ALTERA NADA. Apenas le.

set -uo pipefail

DB_CONTAINER="${DB_CONTAINER:-siap-db}"
DB_USER="${POSTGRES_USER:-siap_user}"
DB_NAME="${POSTGRES_DB:-siap_db}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"
FLASK_APP_PATH="${FLASK_APP_PATH:-/opt/siap/app_cors_livre.py}"
API_BASE="${API_BASE:-https://api.visualsmartflow.com.br}"

C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${C_GREEN}[$(date +%T)]${NC} $1"; }
info() { echo -e "${C_BLUE}[$(date +%T)]${NC} $1"; }
warn() { echo -e "${C_YELLOW}[$(date +%T)] WARN:${NC} $1"; }
err()  { echo -e "${C_RED}[$(date +%T)] ERROR:${NC} $1" >&2; }

# Detect how to run psql
run_psql() {
  if command -v docker >/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${DB_CONTAINER}\$"; then
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
  elif command -v psql >/dev/null && [ -n "${DATABASE_URL:-}" ]; then
    PGPASSWORD="$DB_PASSWORD" psql "$DATABASE_URL" "$@"
  else
    err "Sem acesso ao banco. Configure DB_CONTAINER ou DATABASE_URL."
    return 1
  fi
}

# ─────────────────────────────────────────────────────────────
# 1) SELECT version_num FROM alembic_version
# ─────────────────────────────────────────────────────────────
log "1) Estado da tabela alembic_version em producao..."

VERSION=$(run_psql -tAc "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "<erro>")
if [ -z "$VERSION" ] || [ "$VERSION" = "<erro>" ]; then
  warn "Tabela alembic_version ausente ou inacessivel."
  warn "Isso indica que o sistema pode ter sido inicializado via db.create_all() sem migrar para Alembic."
else
  info "alembic_version = ${VERSION}"
fi

# ─────────────────────────────────────────────────────────────
# 2) Quantas migrations existem no repo local
# ─────────────────────────────────────────────────────────────
log "2) Comparacao com migrations presentes no repo local..."

LOCAL_MIG_COUNT=$(ls migrations/versions/*.py 2>/dev/null | wc -l)
info "Migrations no repo: ${LOCAL_MIG_COUNT}"

# ─────────────────────────────────────────────────────────────
# 3) Heads via flask db heads (requer FLASK_APP no caminho)
# ─────────────────────────────────────────────────────────────
log "3) Tentando executar 'flask db heads' e 'flask db current'..."
echo ""

if [ -d "/opt/siap" ]; then
  cd /opt/siap
  export FLASK_APP="$FLASK_APP_PATH"

  info "--- flask db heads ---"
  flask db heads 2>&1 || warn "Falha ao executar 'flask db heads'."

  echo ""
  info "--- flask db current ---"
  flask db current 2>&1 || warn "Falha ao executar 'flask db current'."
else
  warn "Diretorio /opt/siap nao encontrado — pulando flask db heads/current."
  warn "Execute manualmente dentro do container backend:"
  echo "    docker exec -it siap-backend bash"
  echo "    cd /app"
  echo "    flask db heads"
  echo "    flask db current"
fi

# ─────────────────────────────────────────────────────────────
# 4) Resumo final
# ─────────────────────────────────────────────────────────────
echo ""
log "RESUMO DA AUDITORIA"
echo "  alembic_version:   ${VERSION:-<ausente>}"
echo "  migrations locais: ${LOCAL_MIG_COUNT}"
echo "  (multi-head e divergencias: ver saida de 'flask db heads' acima)"

if [ -z "$VERSION" ]; then
  warn "Alembic nao inicializou. Banco pode estar no estado pre-migration."
  warn "Recomendacao (FORA do escopo P0-A): planejar migracao completa do create_all para Alembic."
fi
