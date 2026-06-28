#!/usr/bin/env bash
# ================================================================
# AraOS — Smoke Test
# Verifica 6 endpoints críticos pós-deploy
# Uso: ./scripts/smoke.sh [--env=staging|production]
# ================================================================
set -euo pipefail

ENV="production"
for arg in "$@"; do [[ "$arg" == --env=* ]] && ENV="${arg#*=}"; done

case "$ENV" in
  staging)
    BASE="https://api.staging.visualsmartflow.com.br"
    ;;
  production)
    BASE="https://api.visualsmartflow.com.br"
    ;;
  *) echo "ENV inválida"; exit 1 ;;
esac

# Usa timeout agressivo para falhar rápido
TIMEOUT=10

check() {
  local path="$1" expect="$2" label="$3"
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$BASE$path" || echo "000")
  if [[ "$code" =~ $expect ]]; then
    echo "  ✓ $label [$code]"
  else
    echo "  ✗ $label [$code — esperado $expect]"
    return 1
  fi
}

echo "→ Smoke $ENV em $BASE"

# 1. API status pública
check "/api/status" "200" "API status"

# 2. CSRF token
check "/api/csrf-token" "200" "CSRF token"

# 3. Login (espera 200 ou 401, nunca 500)
check "/api/auth/login" "^(200|400|401)$" "Auth endpoint reachable"

# 4. Health interno (se exposto)
check "/api/health" "^(200|404)$" "Health endpoint"

# 5. CSRF token presente no response
CSRF=$(curl -sk --max-time "$TIMEOUT" "$BASE/api/csrf-token" | grep -o '"csrf_token":"[^"]*"' | cut -d'"' -f4)
if [[ -n "$CSRF" ]] && [[ ${#CSRF} -ge 32 ]]; then
  echo "  ✓ CSRF token presente (${#CSRF} chars)"
else
  echo "  ✗ CSRF token ausente ou fraco"
  exit 1
fi

echo "✓ Smoke OK"
