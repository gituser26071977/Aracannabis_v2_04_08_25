#!/bin/bash
# scripts/p0a_fix_data_revogacao.sh
#
# P0-A FASE 2 — Correcao Imediata do Banco
#
# Aplica `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP`
# no banco de PRODUCAO do AraOS SIAP.
#
# Pre-requisitos:
#   - Acesso SSH ao VPS (root@147.93.33.253) OU `docker exec` no container `siap-db`
#   - Credenciais do banco (DATABASE_URL ou POSTGRES_PASSWORD)
#
# Uso:
#   1) SSH no VPS:   ssh root@147.93.33.253
#   2) Executar:     bash /opt/siap/scripts/p0a_fix_data_revogacao.sh
#   OU
#   1) Copie o SQL dentro do container db:
#        docker exec siap-db psql -U siap_user -d siap_db -c "ALTER TABLE ..."
#
# Este script e IDEMPOTENTE — pode ser rodado 2x sem efeito colateral.
#
# NAO ALTERA:
#   - Nenhuma migration
#   - Nenhum model
#   - Nenhuma rota
#   - Nenhum dado de paciente

set -euo pipefail

# Configuracoes
DB_CONTAINER="${DB_CONTAINER:-siap-db}"
DB_USER="${POSTGRES_USER:-siap_user}"
DB_NAME="${POSTGRES_DB:-siap_db}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/siap-p0a-backup-$(date +%Y%m%d-%H%M%S)}"
TABLE="pacientes"
COLUMN="data_revogacao"

C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${C_GREEN}[$(date +%T)]${NC} $1"; }
info() { echo -e "${C_BLUE}[$(date +%T)]${NC} $1"; }
warn() { echo -e "${C_YELLOW}[$(date +%T)] WARN:${NC} $1"; }
err()  { echo -e "${C_RED}[$(date +%T)] ERROR:${NC} $1" >&2; }

# Detect how to run psql: prefer docker exec on siap-db, fallback to local psql
run_psql() {
  if command -v docker >/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${DB_CONTAINER}\$"; then
    docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" "$@"
  elif command -v psql >/dev/null && [ -n "${DATABASE_URL:-}" ]; then
    PGPASSWORD="$DB_PASSWORD" psql "$DATABASE_URL" "$@"
  else
    err "Nao foi possivel acessar o banco. Configure DB_CONTAINER ou DATABASE_URL."
    exit 2
  fi
}

# ─────────────────────────────────────────────────────────────
# VERIFICACAO INICIAL — coluna existe?
# ─────────────────────────────────────────────────────────────
log "PASSO 1/4 — Verificando se coluna ${COLUMN} ja existe em ${TABLE}..."

EXISTS=$(run_psql -tAc "SELECT 1 FROM information_schema.columns WHERE table_name='${TABLE}' AND column_name='${COLUMN}' LIMIT 1;" 2>/dev/null || echo "")

if [ "$EXISTS" = "1" ]; then
  warn "Coluna ${COLUMN} JA EXISTE em ${TABLE}. Nada a fazer (idempotente)."
  log "Encerrando sem alteracoes."
  exit 0
fi

info "Coluna ${COLUMN} NAO existe em ${TABLE}. Procedendo com fix."

# ─────────────────────────────────────────────────────────────
# BACKUP LOGICO (pg_dump apenas da tabela pacientes)
# ─────────────────────────────────────────────────────────────
log "PASSO 2/4 — Criando backup logico de ${TABLE} em ${BACKUP_DIR}..."

mkdir -p "$BACKUP_DIR"

if command -v docker >/dev/null && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${DB_CONTAINER}\$"; then
  docker exec -e PGPASSWORD="$DB_PASSWORD" "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --no-privileges --table="$TABLE" \
    > "${BACKUP_DIR}/${TABLE}-${COLUMN}-pre-fix-$(date +%Y%m%d-%H%M%S).sql"
elif command -v pg_dump >/dev/null && [ -n "${DATABASE_URL:-}" ]; then
  PGPASSWORD="$DB_PASSWORD" pg_dump "$DATABASE_URL" --no-owner --no-privileges --table="$TABLE" \
    > "${BACKUP_DIR}/${TABLE}-${COLUMN}-pre-fix-$(date +%Y%m%d-%H%M%S).sql"
else
  warn "pg_dump indisponivel — seguindo SEM backup logico (NAO recomendado em prod)."
  read -r -p "Continuar mesmo assim? (digite 'sim' para confirmar) " CONFIRM
  if [ "$CONFIRM" != "sim" ]; then
    err "Abortado pelo operador."
    exit 1
  fi
fi

ls -la "$BACKUP_DIR" || true
info "Backup salvo em ${BACKUP_DIR}."

# ─────────────────────────────────────────────────────────────
# APLICAR SQL
# ─────────────────────────────────────────────────────────────
log "PASSO 3/4 — Aplicando ALTER TABLE..."

run_psql -c "ALTER TABLE ${TABLE} ADD COLUMN IF NOT EXISTS ${COLUMN} TIMESTAMP;"

log "Comando executado com sucesso."

# ─────────────────────────────────────────────────────────────
# VALIDACAO POS-FIX
# ─────────────────────────────────────────────────────────────
log "PASSO 4/4 — Validando criacao da coluna..."

POST_EXISTS=$(run_psql -tAc "SELECT 1 FROM information_schema.columns WHERE table_name='${TABLE}' AND column_name='${COLUMN}' LIMIT 1;" 2>/dev/null || echo "")

if [ "$POST_EXISTS" = "1" ]; then
  log "OK — coluna ${COLUMN} agora existe em ${TABLE}."
  run_psql -c "\d ${TABLE}" | grep -E "${COLUMN}|^---|^Table" | head -20
  log "Fix concluido com sucesso. Agora execute a migration via:"
  echo "    flask db upgrade"
  echo "ou, se ja rodou o SQL direto, registre formalmente com:"
  echo "    flask db stamp REDACTED"
  exit 0
else
  err "FALHA — coluna ${COLUMN} NAO foi criada. Investigue os logs."
  exit 1
fi
