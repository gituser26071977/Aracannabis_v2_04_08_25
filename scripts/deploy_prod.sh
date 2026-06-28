#!/usr/bin/env bash
# ================================================================
# AraOS — Deploy PRODUÇÃO
# Requer TAG v*.*.* e aprovação manual em GitHub Environment 'production'.
# Uso: ./scripts/deploy_prod.sh v1.2.3
# ================================================================
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then echo "Uso: $0 <version>"; exit 1; fi
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "✗ Versão inválida. Formato esperado: vX.Y.Z"; exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"

if [[ ! -f "$ENV_FILE" ]]; then echo "✗ .env.production não existe"; exit 1; fi

START=$(date +%s)
echo "════════════════════════════════════════"
echo "  AraOS — DEPLOY PRODUÇÃO $VERSION"
echo "  $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "════════════════════════════════════════"

# 1. Pré-deploy: backup completo
echo "→ Backup completo pré-deploy..."
"$SCRIPT_DIR/backup.sh" --env=production

# 2. Git checkout da tag
echo "→ Checkout $VERSION..."
git fetch --tags
git checkout "$VERSION"

# 3. Pull imagens
echo "→ Pull imagens..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull || \
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build

# 4. Rolling restart
echo "→ Restart serviços..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps siap-backend

# 5. Smoke
"$SCRIPT_DIR/smoke.sh" --env=production || {
  echo "✗ Smoke falhou — ROLLBACK IMEDIATO"
  "$SCRIPT_DIR/rollback.sh" --env=production
  exit 1
}

# 6. Frontend
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps siap-frontend
"$SCRIPT_DIR/smoke.sh" --env=production || {
  echo "✗ Smoke pós-frontend falhou — ROLLBACK"
  "$SCRIPT_DIR/rollback.sh" --env=production
  exit 1
}

END=$(date +%s)
echo "════════════════════════════════════════"
echo "  ✓ Deploy produção $VERSION concluído em $((END-START))s"
echo "════════════════════════════════════════"
