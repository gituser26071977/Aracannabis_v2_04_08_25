#!/usr/bin/env bash
# ================================================================
# AraOS — Deploy STAGING
# Provisiona/atualiza ambiente staging a partir do branch develop
# Pré-requisitos: docker, docker-compose, acesso SSH ao VPS staging
# Uso: ./scripts/deploy_staging.sh [--skip-tests]
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.staging.yml"
ENV_FILE="$PROJECT_ROOT/.env.staging"

SKIP_TESTS=false
if [[ "${1:-}" == "--skip-tests" ]]; then SKIP_TESTS=true; fi

START=$(date +%s)
echo "════════════════════════════════════════"
echo "  AraOS — DEPLOY STAGING"
echo "  $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════════"

# 1. Pré-condições
if [[ ! -f "$ENV_FILE" ]]; then
  echo "✗ .env.staging não existe. Copie .env.staging.example."
  exit 1
fi
command -v docker >/dev/null || { echo "✗ docker não instalado"; exit 1; }
command -v docker-compose >/dev/null || { echo "✗ docker-compose não instalado"; exit 1; }

# 2. Testes (opcional)
if ! $SKIP_TESTS; then
  echo "→ Rodando suíte P0..."
  (cd "$PROJECT_ROOT" && .venv-test/bin/python -m pytest tests/security/test_p0_remediation_m18.py -q)
fi

# 3. Backup pré-deploy (defesa em profundidade)
echo "→ Backup pré-deploy..."
"$SCRIPT_DIR/backup.sh" --env=staging

# 4. Pull + build
echo "→ Build de imagens..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --pull

# 5. Down + Up (com healthcheck aguardando)
echo "→ Subindo serviços..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# 6. Aguardar healthy
echo "→ Aguardando healthcheck..."
TIMEOUT=120; ELAPSED=0
while [[ $ELAPSED -lt $TIMEOUT ]]; do
  if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps | grep -q "(healthy)"; then
    break
  fi
  sleep 5; ELAPSED=$((ELAPSED+5))
done

# 7. Smoke test
echo "→ Smoke test..."
"$SCRIPT_DIR/smoke.sh" --env=staging || { echo "✗ Smoke falhou — iniciando rollback"; "$SCRIPT_DIR/rollback.sh" --env=staging; exit 1; }

END=$(date +%s)
echo "════════════════════════════════════════"
echo "  ✓ Deploy staging concluído em $((END-START))s"
echo "════════════════════════════════════════"
