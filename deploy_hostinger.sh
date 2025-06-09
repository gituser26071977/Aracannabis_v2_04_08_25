#!/bin/bash
# Script de Deploy para Hostinger - Aracannabis
# Versão: 1.0
# Data: $(date +%Y-%m-%d)

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "=================================================================="
echo "🚀 DEPLOY ARACANNABIS NA HOSTINGER"
echo "=================================================================="
echo -e "${NC}"

# Verificar se estamos no diretório correto
if [ ! -f "app.py" ]; then
    error "Arquivo app.py não encontrado. Execute este script no diretório raiz do projeto."
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    error "Arquivo .env não encontrado."
    info "Copie .env.production.example para .env e configure as variáveis:"
    info "cp .env.production.example .env"
    exit 1
fi

# Verificar se é ambiente de produção
source .env
if [ "$FLASK_ENV" != "production" ]; then
    warn "FLASK_ENV não está definido como 'production' no arquivo .env"
    read -p "Continuar mesmo assim? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# 1. Backup do banco atual (se existir)
log "1. Fazendo backup do banco de dados..."
if [ ! -z "$DATABASE_URL" ]; then
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    if command -v pg_dump &> /dev/null; then
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || warn "Não foi possível fazer backup (banco pode não existir ainda)"
        if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
            log "Backup salvo em: $BACKUP_FILE"
        else
            rm -f "$BACKUP_FILE"
            info "Nenhum backup criado (banco novo ou vazio)"
        fi
    else
        warn "pg_dump não encontrado. Pulando backup."
    fi
else
    warn "DATABASE_URL não configurada. Pulando backup."
fi

# 2. Testar conexão com banco
log "2. Testando conexão com banco de dados..."
if python3 test_db_connection_hostinger.py; then
    log "Conexão com banco OK!"
else
    error "Falha na conexão com banco. Verifique as configurações."
    exit 1
fi

# 3. Criar ambiente virtual se não existir
log "3. Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    log "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# 4. Instalar dependências
log "4. Instalando dependências..."
if [ "$AI_ENABLED" = "true" ]; then
    info "Instalando versão completa (com IA)..."
    pip install -r requirements.txt
else
    info "Instalando versão básica (sem IA)..."
    pip install -r requirements_basic.txt
fi

# 5. Executar migrações do banco
log "5. Executando migrações do banco de dados..."
python3 migrate_db.py

# 6. Criar usuário administrador
log "6. Configurando usuário administrador..."
if python3 -c "from models import Usuario; from app import create_app; app = create_app(); app.app_context().push(); print('Usuários:', Usuario.query.count())" 2>/dev/null | grep -q "Usuários: 0"; then
    log "Criando usuário administrador..."
    python3 create_secure_admin.py
else
    info "Usuário administrador já existe."
fi

# 7. Build do frontend
log "7. Fazendo build do frontend..."
cd frontend

# Verificar se Node.js está instalado
if ! command -v npm &> /dev/null; then
    error "Node.js/npm não encontrado. Instale o Node.js primeiro."
    exit 1
fi

# Instalar dependências do frontend
log "Instalando dependências do frontend..."
npm install

# Configurar variáveis de ambiente do frontend
if [ "$AI_ENABLED" = "true" ]; then
    export REACT_APP_AI_ENABLED=true
else
    export REACT_APP_AI_ENABLED=false
fi

export REACT_APP_API_URL=${API_URL:-"http://localhost:5000"}

# Build do frontend
log "Compilando frontend..."
npm run build

cd ..

# 8. Configurar servidor web (Nginx)
log "8. Configurando servidor web..."
if command -v nginx &> /dev/null; then
    if [ -f "nginx.conf" ]; then
        log "Configurando Nginx..."
        sudo cp nginx.conf /etc/nginx/sites-available/aracannabis
        sudo ln -sf /etc/nginx/sites-available/aracannabis /etc/nginx/sites-enabled/
        
        # Testar configuração do Nginx
        if sudo nginx -t; then
            log "Configuração do Nginx OK!"
            sudo systemctl reload nginx
        else
            warn "Erro na configuração do Nginx. Verifique manualmente."
        fi
    else
        warn "Arquivo nginx.conf não encontrado."
    fi
else
    info "Nginx não encontrado. Configure manualmente o servidor web."
fi

# 9. Configurar serviço systemd
log "9. Configurando serviço systemd..."
if [ -f "aracannabis.service" ]; then
    sudo cp aracannabis.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable aracannabis
    log "Serviço systemd configurado!"
else
    warn "Arquivo aracannabis.service não encontrado."
fi

# 10. Gerar chaves de segurança se necessário
log "10. Verificando chaves de segurança..."
if grep -q "GERAR_CHAVE_SEGURA" .env; then
    warn "Chaves de segurança não foram configuradas!"
    info "Execute os comandos abaixo para gerar chaves seguras:"
    echo "JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
    read -p "Pressione Enter para continuar..."
fi

# 11. Testar aplicação
log "11. Testando aplicação..."
if python3 -c "from app import create_app; app = create_app(); print('App criado com sucesso!')"; then
    log "Aplicação testada com sucesso!"
else
    error "Erro ao testar aplicação."
    exit 1
fi

# 12. Iniciar aplicação
log "12. Iniciando aplicação..."

# Escolher método de inicialização
if command -v systemctl &> /dev/null && [ -f "/etc/systemd/system/aracannabis.service" ]; then
    log "Iniciando via systemd..."
    sudo systemctl start aracannabis
    sudo systemctl status aracannabis --no-pager
elif command -v gunicorn &> /dev/null; then
    log "Iniciando via gunicorn..."
    WORKERS=${WORKERS:-4}
    PORT=${PORT:-5000}
    
    # Matar processos existentes
    pkill -f "gunicorn.*app:app" || true
    
    # Iniciar em background
    nohup gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS app:app > gunicorn.log 2>&1 &
    
    sleep 3
    
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        log "Gunicorn iniciado com sucesso! PID: $(pgrep -f 'gunicorn.*app:app')"
    else
        error "Falha ao iniciar gunicorn. Verifique gunicorn.log"
        exit 1
    fi
else
    warn "Nem systemd nem gunicorn encontrados. Iniciando com Flask development server..."
    python3 app.py &
fi

# 13. Verificar se a aplicação está rodando
log "13. Verificando se a aplicação está funcionando..."
sleep 5

PORT=${PORT:-5000}
if curl -s "http://localhost:$PORT/api/status" > /dev/null; then
    log "✅ Aplicação está rodando em http://localhost:$PORT"
else
    warn "Aplicação pode não estar respondendo. Verifique os logs."
fi

# 14. Mostrar informações finais
echo -e "${GREEN}"
echo "=================================================================="
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "=================================================================="
echo -e "${NC}"

info "URLs da aplicação:"
echo "  - API: http://localhost:$PORT"
echo "  - Status: http://localhost:$PORT/api/status"
if [ ! -z "$HOSTINGER_DOMAIN" ]; then
    echo "  - Produção: https://$HOSTINGER_DOMAIN"
fi

info "Comandos úteis:"
echo "  - Ver logs: tail -f gunicorn.log"
echo "  - Parar aplicação: pkill -f 'gunicorn.*app:app'"
echo "  - Reiniciar: sudo systemctl restart aracannabis"
echo "  - Status do serviço: sudo systemctl status aracannabis"

info "Arquivos importantes:"
echo "  - Logs: gunicorn.log"
echo "  - Backup: $BACKUP_FILE (se criado)"
echo "  - Configuração: .env"

warn "Próximos passos:"
echo "  1. Configure o domínio/DNS na Hostinger"
echo "  2. Configure certificado SSL"
echo "  3. Teste todas as funcionalidades"
echo "  4. Configure backup automático"
echo "  5. Configure monitoramento"

log "Deploy finalizado em $(date)"
