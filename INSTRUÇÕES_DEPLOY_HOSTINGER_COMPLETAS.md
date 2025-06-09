# 🚀 Instruções Completas para Deploy na Hostinger

## 📋 Resumo da Revisão do Sistema

### ✅ Status Atual
O sistema Aracannabis foi revisado e está pronto para deploy na Hostinger. Foram criados:

1. **Versão básica sem IA** (`app_sem_ia.py`) - Mantida separada
2. **Versão completa com IA** (`app.py`) - Versão atual
3. **Sistema condicional** - Permite ativar/desativar IA via variável de ambiente
4. **Scripts de deploy automatizados**
5. **Configurações específicas para Hostinger**

### 🔧 Arquivos Criados para Deploy

- `requirements_basic.txt` - Dependências sem IA
- `test_db_connection_hostinger.py` - Teste de conexão PostgreSQL
- `.env.production.example` - Configurações de produção
- `deploy_hostinger.sh` - Script automatizado de deploy
- `REVISAO_SISTEMA_DEPLOY_HOSTINGER.md` - Documentação técnica

## 🎯 Passo a Passo para Deploy

### 1. Preparação na Hostinger

#### 1.1 Acessar Painel PostgreSQL
1. Faça login no painel da Hostinger
2. Vá em **"Banco de Dados"** → **"PostgreSQL"**
3. Anote as informações:
   - **Hostname**: (ex: postgresql.hostinger.com)
   - **Porta**: 5432
   - **Usuário**: seu_usuario
   - **Senha**: sua_senha
   - **Banco padrão**: (ex: u123456789_default)

#### 1.2 Criar Banco Específico (Recomendado)
```sql
-- Conecte via phpPgAdmin ou psql e execute:
CREATE DATABASE aracannabis_prod 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='pt_BR.UTF-8' 
    LC_CTYPE='pt_BR.UTF-8';

-- Criar usuário específico (opcional)
CREATE USER aracannabis_user WITH PASSWORD 'senha_super_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE aracannabis_prod TO aracannabis_user;
```

### 2. Configuração Local

#### 2.1 Copiar Arquivo de Configuração
```bash
cp .env.production.example .env
```

#### 2.2 Editar Arquivo .env
```bash
# Flask Configuration for Production (Hostinger)
FLASK_ENV=production
FLASK_APP=app.py

# Database Configuration (Hostinger PostgreSQL)
DATABASE_URL=postgresql://seu_usuario:sua_senha@hostname:5432/aracannabis_prod

# Security Keys (GERAR NOVAS!)
JWT_SECRET_KEY=REDACTED
SECRET_KEY=REDACTED

# Debug Mode
DEBUG=False

# AI Features (false para versão básica)
AI_ENABLED=false

# Email Configuration (Hostinger SMTP)
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
EMAIL_USER=aracannabis@agentesinteligentes.pro
EMAIL_PASSWORD=sua_senha_email
```

#### 2.3 Gerar Chaves Seguras
```bash
# Gerar JWT Secret Key
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# Gerar Secret Key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

### 3. Testar Conexão com Banco

```bash
# Testar conexão
python3 test_db_connection_hostinger.py

# Ver instruções de configuração
python3 test_db_connection_hostinger.py --info
```

### 4. Deploy Automatizado

```bash
# Executar script de deploy
./deploy_hostinger.sh
```

O script irá:
1. ✅ Fazer backup do banco (se existir)
2. ✅ Testar conexão com PostgreSQL
3. ✅ Criar ambiente virtual
4. ✅ Instalar dependências (básicas ou completas)
5. ✅ Executar migrações do banco
6. ✅ Criar usuário administrador
7. ✅ Fazer build do frontend
8. ✅ Configurar Nginx (se disponível)
9. ✅ Configurar serviço systemd
10. ✅ Iniciar aplicação
11. ✅ Verificar funcionamento

### 5. Deploy Manual (Alternativo)

Se preferir fazer manualmente:

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements_basic.txt  # Versão básica
# OU
pip install -r requirements.txt        # Versão completa

# 3. Configurar banco
python3 migrate_db.py

# 4. Criar admin
python3 create_secure_admin.py

# 5. Build frontend
cd frontend
npm install
npm run build
cd ..

# 6. Iniciar aplicação
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 🔧 Configurações Específicas da Hostinger

### Nginx Configuration
Se usar Nginx, o arquivo `nginx.conf` já está configurado. Copie para:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/aracannabis
sudo ln -sf /etc/nginx/sites-available/aracannabis /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Systemd Service
O arquivo `aracannabis.service` configura o serviço:
```bash
sudo cp aracannabis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aracannabis
sudo systemctl start aracannabis
```

### SSL/HTTPS
Configure certificado SSL na Hostinger:
1. Vá em **"SSL"** no painel
2. Ative **"Let's Encrypt"** ou faça upload do certificado
3. Force redirecionamento HTTPS

## 📊 Verificações Pós-Deploy

### 1. Testar API
```bash
curl http://localhost:5000/api/status
```

### 2. Testar Frontend
Acesse: `http://seu-dominio.com`

### 3. Testar Login
- Usuário: admin
- Senha: (definida durante criação)

### 4. Verificar Logs
```bash
tail -f gunicorn.log
# OU
sudo journalctl -u aracannabis -f
```

## 🔄 Comandos Úteis

### Gerenciamento da Aplicação
```bash
# Ver status
sudo systemctl status aracannabis

# Reiniciar
sudo systemctl restart aracannabis

# Parar
sudo systemctl stop aracannabis

# Ver logs
sudo journalctl -u aracannabis -f
```

### Backup do Banco
```bash
# Backup manual
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
psql $DATABASE_URL < backup_file.sql
```

### Atualização do Sistema
```bash
# Parar aplicação
sudo systemctl stop aracannabis

# Atualizar código
git pull origin main

# Reinstalar dependências se necessário
source venv/bin/activate
pip install -r requirements_basic.txt

# Executar migrações
python3 migrate_db.py

# Rebuild frontend se necessário
cd frontend && npm run build && cd ..

# Reiniciar aplicação
sudo systemctl start aracannabis
```

## 🚨 Troubleshooting

### Problema: Erro de Conexão com Banco
```bash
# Verificar configuração
python3 test_db_connection_hostinger.py

# Verificar variáveis de ambiente
echo $DATABASE_URL
```

### Problema: Aplicação Não Inicia
```bash
# Verificar logs
sudo journalctl -u aracannabis -f

# Testar manualmente
source venv/bin/activate
python3 app.py
```

### Problema: Frontend Não Carrega
```bash
# Verificar build
cd frontend
npm run build

# Verificar configuração do Nginx
sudo nginx -t
```

### Problema: Erro 500
```bash
# Verificar logs da aplicação
tail -f gunicorn.log

# Verificar permissões
ls -la /var/log/aracannabis/
```

## 📈 Monitoramento e Manutenção

### Logs Importantes
- **Aplicação**: `gunicorn.log` ou `journalctl -u aracannabis`
- **Nginx**: `/var/log/nginx/error.log`
- **PostgreSQL**: `/var/log/postgresql/`

### Backup Automático
Configure cron para backup diário:
```bash
# Editar crontab
crontab -e

# Adicionar linha para backup às 2h da manhã
0 2 * * * /path/to/backup_script.sh
```

### Monitoramento de Recursos
```bash
# CPU e Memória
htop

# Espaço em disco
df -h

# Conexões do banco
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

## 🎉 Conclusão

O sistema Aracannabis está pronto para produção na Hostinger com:

✅ **Versão básica sem IA** - Mais leve e estável
✅ **Configuração de segurança** - HTTPS, rate limiting, LGPD
✅ **Deploy automatizado** - Script completo
✅ **Backup e monitoramento** - Ferramentas incluídas
✅ **Documentação completa** - Instruções detalhadas

### Próximos Passos Recomendados:
1. 🔧 Configure domínio e SSL na Hostinger
2. 📊 Configure monitoramento (Sentry, logs)
3. 🔄 Configure backup automático
4. 🧪 Teste todas as funcionalidades
5. 📚 Treine usuários no sistema

### Suporte:
- 📖 Documentação: `REVISAO_SISTEMA_DEPLOY_HOSTINGER.md`
- 🔧 Scripts: `deploy_hostinger.sh`, `test_db_connection_hostinger.py`
- ⚙️ Configurações: `.env.production.example`

**Sistema pronto para uso em produção! 🚀**
