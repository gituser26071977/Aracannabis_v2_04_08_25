#!/usr/bin/env bash
# ================================================================
# Deploy reproduzível do stack aracannabis.com.br no VPS.
#
# Constrói as imagens A PARTIR DO FONTE do repo, recria os containers e
# aplica as rotas do Traefik — substituindo os passos manuais (runtime)
# por um fluxo versionado.
#
# PRÉ-REQUISITO: o checkout em REPO_DIR deve conter o código alinhado
# (domínio aracannabis + CORS + feature de senha). As branches do repo
# precisam estar reconciliadas antes do build de origem.
#
# Uso:
#   DATABASE_URL='postgresql://...' ./deploy.sh
#
# Variáveis (com defaults):
#   REPO_DIR=/root/projetos/araos
#   BACKEND_IMAGE=siap-backend:aracannabis
#   FRONTEND_IMAGE=siap-frontend:aracannabis
#   BACKEND_CONTAINER=siap-backend-final
#   FRONTEND_CONTAINER=siap-frontend-aracannabis
#   FRONTEND_BUILD_API_URL=https://api.aracannabis.com.br
#   CORS_ORIGINS=...
#   DATABASE_URL          (obrigatório; não versionar segredo)
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-/root/projetos/araos}"
BACKEND_IMAGE="${BACKEND_IMAGE:-siap-backend:aracannabis}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-siap-frontend:aracannabis}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-siap-backend-final}"
FRONTEND_CONTAINER="${FRONTEND_CONTAINER:-siap-frontend-aracannabis}"
FRONTEND_BUILD_API_URL="${FRONTEND_BUILD_API_URL:-https://api.aracannabis.com.br}"
CORS_ORIGINS="${CORS_ORIGINS:-https://www.aracannabis.com.br,https://aracannabis.com.br,https://api.aracannabis.com.br,https://siap.vittalis.site,https://vittalis.site,https://api.vittalis.site}"

: "${DATABASE_URL:?defina DATABASE_URL (ex.: postgresql://siap_user:...@siap-db:5432/aracannabis)}"

echo "── 1/4 build backend (do fonte) ──"
docker build -f "$REPO_DIR/Dockerfile.backend" -t "$BACKEND_IMAGE" "$REPO_DIR"

echo "── 2/4 build frontend (do fonte) ──"
docker build --build-arg REACT_APP_API_URL="$FRONTEND_BUILD_API_URL" \
  -t "$FRONTEND_IMAGE" -f "$REPO_DIR/frontend/Dockerfile" "$REPO_DIR/frontend"

echo "── 3/4 recriar containers ──"
docker rm -f "$BACKEND_CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$BACKEND_CONTAINER" --restart unless-stopped \
  --network araos_siap-internal \
  -e FLASK_APP=app_cors_livre.py \
  -e DATABASE_URL="$DATABASE_URL" \
  -e CORS_ORIGINS="$CORS_ORIGINS" \
  -e PORT=5002 \
  -e ARAOS_SITE_URL="https://www.aracannabis.com.br" \
  -v "$REPO_DIR/.env.production:/app/.env:ro" \
  "$BACKEND_IMAGE" \
  gunicorn --bind 0.0.0.0:5002 --timeout 300 --workers 3 --threads 2 wsgi_prod:application
docker network connect web "$BACKEND_CONTAINER"

docker rm -f "$FRONTEND_CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$FRONTEND_CONTAINER" --restart unless-stopped \
  --network web \
  -e REACT_APP_API_URL="$FRONTEND_BUILD_API_URL" \
  "$FRONTEND_IMAGE"

echo "── 4/4 aplicar rotas Traefik ──"
bash "$SCRIPT_DIR/apply-traefik.sh"

echo "✓ Deploy aracannabis concluído."
echo "  Frontend: https://www.aracannabis.com.br"
echo "  API:      https://api.aracannabis.com.br/api/status"
