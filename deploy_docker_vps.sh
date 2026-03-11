#!/bin/bash
# Script de Deploy via Docker para Hostinger - Aracannabis SIAP
# Versão: 2.0 (Docker Edition)

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%T')] $1${NC}"; }
info() { echo -e "${BLUE}[$(date +'%T')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%T')] ⚠️  $1${NC}"; }
error() { echo -e "${RED}[$(date +'%T')] ❌ $1${NC}"; }

log "🚀 Iniciando Deploy Aracannabis SIAP (Docker)..."

# 1. Verificar arquivos essenciais
if [ ! -f "docker-compose.prod.yml" ]; then
    error "Arquivo docker-compose.prod.yml não encontrado!"
    exit 1
fi

if [ ! -f ".env.production" ]; then
    error "Arquivo .env.production não encontrado!"
    warn "Crie o arquivo primeiro com as chaves de API reais."
    exit 1
fi

# 2. Configurar ambiente Docker
log "1. Configurando rede externa do Traefik..."
docker network create web 2>/dev/null || info "Rede 'web' já existe."

# 3. Pull/Build e Start
log "2. Subindo containers de produção..."
# Copiar env.production para .env temporariamente para o docker-compose usar
cp .env.production .env
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Inicializar Banco de Dados
log "3. Aplicando schema do banco de dados..."
sleep 5 # Aguardar DB subir
docker exec siap-backend python3 apply_schema.py

# 5. Backup (Opcional)
warn "Lembre-se de configurar backups automáticos do volume 'siap_postgres_data'."

# 6. Teste de Conectividade IA
log "4. Validando integração com LLMs..."
docker exec siap-backend python3 test_llm_connectivity.py

log "✅ Deploy concluído com sucesso!"
info "Backend: https://api.aracannabis.com.br"
info "Frontend: https://aracannabis.com.br"
log "Dica: Use 'docker-compose -f docker-compose.prod.yml logs -f' para acompanhar."
