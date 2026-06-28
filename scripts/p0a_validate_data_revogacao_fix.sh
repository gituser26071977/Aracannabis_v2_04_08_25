#!/bin/bash
# scripts/p0a_validate_data_revogacao_fix.sh
#
# P0-A FASE 2 — Validacao Funcional pos-fix
#
# Testa os 3 endpoints que estavam quebrados pelo bug `data_revogacao`:
#   - GET /api/dashboard/stats
#   - GET /api/pacientes
#   - GET /api/pacientes/<id>
#
# Espera-se que TODOS retornem 200 OK apos o fix.

set -euo pipefail

API_BASE="${API_BASE:-https://api.visualsmartflow.com.br}"
ADMIN_USER="${ADMIN_USER:-tester.modulos@araos.dev}"
ADMIN_PASS="${ADMIN_PASS:-Tester@2025}"
LOGIN_URL="${API_BASE}/api/auth/login"

C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${C_GREEN}[$(date +%T)]${NC} $1"; }
info() { echo -e "${C_BLUE}[$(date +%T)]${NC} $1"; }
err()  { echo -e "${C_RED}[$(date +%T)] ERROR:${NC} $1" >&2; }

# ─────────────────────────────────────────────────────────────
# Login para obter JWT
# ─────────────────────────────────────────────────────────────
log "Efetuando login em ${LOGIN_URL}..."

LOGIN_RESPONSE=$(curl -sS -m 10 -X POST -H "Content-Type: application/json" \
  -d "{\"usuario\":\"${ADMIN_USER}\",\"senha\":\"${ADMIN_PASS}\"}" \
  "${LOGIN_URL}" 2>&1) || {
  err "Falha no login. Verifique credenciais e conectividade."
  echo "$LOGIN_RESPONSE"
  exit 1
}

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  err "Nao foi possivel extrair access_token da resposta de login."
  echo "Resposta: $LOGIN_RESPONSE"
  exit 1
fi

info "Token JWT obtido (len=${#TOKEN})."

# ─────────────────────────────────────────────────────────────
# Testar endpoints
# ─────────────────────────────────────────────────────────────
test_endpoint() {
  local label="$1"
  local url="$2"
  local expected_status="$3"

  log "Testando ${label}: ${url}"

  HTTP_CODE=$(curl -sS -m 15 -o /tmp/p0a_resp_body -w "%{http_code}" \
    -H "Authorization: Bearer ${TOKEN}" \
    "${url}" 2>/dev/null || echo "000")

  TIME_TOTAL=$(curl -sS -m 15 -o /dev/null -w "%{time_total}\n" \
    -H "Authorization: Bearer ${TOKEN}" \
    "${url}" 2>/dev/null || echo "0")

  BODY_PREVIEW=$(head -c 200 /tmp/p0a_resp_body 2>/dev/null | tr -d '\n')

  if [ "$HTTP_CODE" = "$expected_status" ]; then
    info "  [OK] HTTP ${HTTP_CODE} em ${TIME_TOTAL}s"
    info "        body: ${BODY_PREVIEW}..."
    return 0
  else
    err "  [FAIL] esperado ${expected_status}, obtido HTTP ${HTTP_CODE} em ${TIME_TOTAL}s"
    err "        body: ${BODY_PREVIEW}..."
    return 1
  fi
}

FAIL=0

# 1) GET /api/dashboard/stats
test_endpoint "GET /api/dashboard/stats" "${API_BASE}/api/dashboard/stats" "200" || FAIL=1

# 2) GET /api/pacientes
test_endpoint "GET /api/pacientes" "${API_BASE}/api/pacientes?limit=1" "200" || FAIL=1

# 3) GET /api/pacientes/<id> — pega o primeiro ID da lista de pacientes
PRIMEIRO_ID=$(curl -sS -m 10 -H "Authorization: Bearer ${TOKEN}" \
  "${API_BASE}/api/pacientes?limit=1" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pacientes',[{}])[0].get('id',''))" 2>/dev/null || echo "")

if [ -n "$PRIMEIRO_ID" ]; then
  test_endpoint "GET /api/pacientes/${PRIMEIRO_ID}" "${API_BASE}/api/pacientes/${PRIMEIRO_ID}" "200" || FAIL=1
else
  warn "Nenhum paciente retornado — pulando teste de GET /api/pacientes/<id>"
fi

# ─────────────────────────────────────────────────────────────
# Resultado
# ─────────────────────────────────────────────────────────────
echo ""
if [ "$FAIL" = "0" ]; then
  log "TODOS os 3 endpoints retornaram 200 OK."
  log "FASE 2 validada com sucesso."
  exit 0
else
  err "PELO MENOS UM endpoint falhou. Investigue o body acima antes de prosseguir."
  exit 1
fi
