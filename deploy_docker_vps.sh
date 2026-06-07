#!/bin/bash
# Script de Deploy via Docker para Hostinger - Aracannabis SIAP
# Versão: 2.1 (Docker Edition - Corrigido)

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
    warn "Use .env.production.example como template."
    exit 1
fi

# 2. Verificar variáveis críticas no .env.production
warn "Verificando configurações críticas..."
if ! grep -q "POSTGRES_PASSWORD=" .env.production || grep -q "POSTGRES_PASSWORD=definir_senha_forte" .env.production; then
    error "POSTGRES_PASSWORD não definida ou usando valor padrão!"
    exit 1
fi

if ! grep -q "SECRET_KEY=" .env.production || grep -q "SECRET_KEY=sua_chave_secreta" .env.production; then
    error "SECRET_KEY não definida ou usando valor padrão!"
    exit 1
fi

# 3. Configurar rede externa do Traefik
log "1. Configurando rede externa do Traefik..."
docker network create web 2>/dev/null || info "Rede 'web' já existe."

# 4. Garantir permissões corretas nos scripts
chmod +x entrypoint_siap.sh 2>/dev/null || true

# 5. Build e Start dos containers
log "2. Subindo containers de produção..."

# Copiar env.production para .env para o docker-compose usar
cp .env.production .env

# Parar containers existentes (se houver)
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build e start
docker-compose -f docker-compose.prod.yml up -d --build

# 6. Aguardar banco de dados estar saudável
log "3. Aguardando banco de dados ficar saudável..."
sleep 5

# Verificar se o DB está respondendo
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T siap-db pg_isready -U siap_user -d aracannabis > /dev/null 2>&1; then
        log "✅ Banco de dados está pronto!"
        break
    fi
    echo "  Aguardando... ($i/30)"
    sleep 2
done

# 7. Inicializar Banco de Dados
log "4. Inicializando banco de dados..."
docker-compose -f docker-compose.prod.yml exec -T siap-backend python init_docker.py || {
    error "Falha ao inicializar banco de dados"
    warn "Verifique os logs: docker-compose -f docker-compose.prod.yml logs siap-backend"
    exit 1
}

# 8. Verificar se o superadmin existe
log "5. Verificando superadmin..."
docker-compose -f docker-compose.prod.yml exec -T siap-backend python check_superadmin.py 2>/dev/null || {
    warn "Superadmin não encontrado. Execute create_superadmin.py se necessário."
}

# 9. Teste de Conectividade IA (opcional)
log "6. Validando integração com LLMs..."
docker-compose -f docker-compose.prod.yml exec -T siap-backend python test_llm_connectivity.py || {
    warn "Alguns provedores de LLM podem não estar configurados corretamente."
    warn "Verifique as chaves de API no .env.production"
}

# 10. Health check
log "7. Verificando saúde dos serviços..."
sleep 3

# Backend
if curl -sf http://localhost:5002/api/status > /dev/null 2>&1 || \
   curl -sf https://api.aracannabis.com.br/api/status > /dev/null 2>&1; then
    log "✅ Backend está respondendo!"
else
    warn "Backend pode não estar totalmente pronto. Verifique os logs."
fi

log "✅ Deploy concluído com sucesso!"
echo ""
info "═══════════════════════════════════════════════════════════"
info "  URLs do Sistema:"
info "  - Frontend: https://aracannabis.com.br"
info "  - API:      https://api.aracannabis.com.br"
info "  - API Status: https://api.aracannabis.com.br/api/status"
info "═══════════════════════════════════════════════════════════"
echo ""
log "Comandos úteis:"
info "  Ver logs:  docker-compose -f docker-compose.prod.yml logs -f"
info "  Parar:     docker-compose -f docker-compose.prod.yml down"
info "  Restart:   docker-compose -f docker-compose.prod.yml restart"
echo ""
warn "Lembre-se de configurar backups automáticos do volume 'siap_postgres_data'!"
