# Revisão do Sistema Aracannabis para Deploy na Hostinger

## Status Atual do Sistema

### ✅ Funcionalidades Básicas Implementadas
- **Autenticação e Autorização**: Sistema de login com JWT
- **Gestão de Pacientes**: CRUD completo de pacientes
- **Sintomas**: Registro e acompanhamento de sintomas
- **Dosagens**: Controle de dosagens de medicamentos
- **Evoluções**: Histórico de evolução dos pacientes
- **Consultas**: Agendamento e gestão de consultas
- **LGPD**: Conformidade com proteção de dados
- **Segurança**: Rate limiting, CORS, headers de segurança

### ⚠️ Componentes de IA Identificados (Precisam ser Condicionados)

#### Backend:
1. **routes/ai_config.py** - Configuração de IA
2. **routes/import_export.py** - Import/Export com IA
3. **services/ai_agents.py** - Agentes de IA
4. **services/ai_agents_optimized.py** - Versão otimizada dos agentes

#### Frontend:
1. **frontend/src/pages/AIConfigPage.js** - Página de configuração de IA
2. **frontend/src/components/ImportExportManager.js** - Gerenciador de import/export com IA
3. **Menu de navegação** - Item "Configuração IA" no App.js

#### Dependências de IA no requirements.txt:
- openai
- crewai
- crewai_tools
- langchain*
- groq

## Plano de Preparação para Deploy

### 1. Criar Versão Condicional (Recomendado)

#### 1.1 Modificar App.js para Condicionar IA
```javascript
// Adicionar variável de ambiente para controlar IA
const AI_ENABLED = process.env.REACT_APP_AI_ENABLED === 'true';

// No menu de navegação, condicionar item de IA:
{ text: 'Configuração IA', icon: <PsychologyIcon />, path: '/ai-config', auth: true, aiRequired: true },

// Filtrar itens que requerem IA:
.filter(item => !item.auth || (item.auth && currentUser))
.filter(item => !item.aiRequired || (item.aiRequired && AI_ENABLED))
```

#### 1.2 Criar requirements_basic.txt (Sem IA)
```
Flask>=2.0.0
Flask-JWT-Extended>=4.0.0
Flask-CORS>=3.0.0
Flask-SQLAlchemy>=3.0.0
Flask-Limiter>=3.0.0
SQLAlchemy
python-dotenv>=1.0.0
psycopg2-binary
Werkzeug
gunicorn
pandas>=2.0.0
```

### 2. Configuração do Banco PostgreSQL na Hostinger

#### 2.1 Informações Necessárias da Hostinger
```bash
# Dados que você precisa obter do painel da Hostinger:
HOST: [hostname_do_postgres]
PORT: [porta_do_postgres] # geralmente 5432
DATABASE: [nome_do_banco_existente]
USERNAME: [seu_usuario_postgres]
PASSWORD: [sua_senha_postgres]
```

#### 2.2 Criar Novo Banco de Dados
```sql
-- Conectar ao PostgreSQL da Hostinger e executar:
CREATE DATABASE aracannabis_prod;
CREATE USER aracannabis_user WITH PASSWORD 'senha_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE aracannabis_prod TO aracannabis_user;
```

#### 2.3 String de Conexão para Produção
```bash
# No arquivo .env de produção:
DATABASE_URL=postgresql://aracannabis_user:senha_segura_aqui@hostname_hostinger:5432/aracannabis_prod
```

### 3. Arquivos de Deploy

#### 3.1 .env para Produção (Hostinger)
```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=app.py

# Database Configuration (Hostinger PostgreSQL)
DATABASE_URL=postgresql://usuario:senha@host:5432/aracannabis_prod

# Security Keys (GERAR NOVAS CHAVES SEGURAS!)
JWT_SECRET_KEY=chave_jwt_super_segura_de_producao
SECRET_KEY=REDACTED

# Debug Mode
DEBUG=False

# AI Features (Desabilitar para versão básica)
AI_ENABLED=false

# Email Configuration (Hostinger SMTP)
SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=465
EMAIL_USER=aracannabis@agentesinteligentes.pro
EMAIL_PASSWORD=sua_senha_email_hostinger
```

#### 3.2 Script de Deploy Atualizado
```bash
#!/bin/bash
# deploy_hostinger.sh

echo "=== Deploy Aracannabis na Hostinger ==="

# 1. Backup do banco atual (se existir)
echo "1. Fazendo backup do banco..."
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Instalar dependências básicas
echo "2. Instalando dependências..."
pip install -r requirements_basic.txt

# 3. Executar migrações
echo "3. Executando migrações do banco..."
python migrate_db.py

# 4. Criar usuário admin
echo "4. Criando usuário administrador..."
python create_secure_admin.py

# 5. Build do frontend
echo "5. Fazendo build do frontend..."
cd frontend
npm install
npm run build
cd ..

# 6. Configurar Nginx (se necessário)
echo "6. Configurando servidor web..."
sudo cp nginx.conf /etc/nginx/sites-available/aracannabis
sudo ln -sf /etc/nginx/sites-available/aracannabis /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 7. Iniciar aplicação
echo "7. Iniciando aplicação..."
gunicorn --bind 0.0.0.0:5000 app:app

echo "=== Deploy concluído! ==="
```

### 4. Checklist de Preparação

#### ✅ Backend
- [ ] Testar app_sem_ia.py localmente
- [ ] Criar requirements_basic.txt
- [ ] Configurar variáveis de ambiente de produção
- [ ] Testar conexão com PostgreSQL da Hostinger
- [ ] Executar migrações do banco
- [ ] Criar usuário administrador
- [ ] Configurar HTTPS/SSL

#### ✅ Frontend
- [ ] Adicionar variável REACT_APP_AI_ENABLED
- [ ] Condicionar componentes de IA
- [ ] Testar build de produção
- [ ] Configurar URLs da API para produção
- [ ] Otimizar assets estáticos

#### ✅ Infraestrutura
- [ ] Configurar domínio/subdomínio
- [ ] Configurar certificado SSL
- [ ] Configurar Nginx/Apache
- [ ] Configurar backup automático
- [ ] Configurar monitoramento

### 5. Comandos para Hostinger

#### 5.1 Acessar PostgreSQL
```bash
# Via terminal da Hostinger:
psql -h hostname -U usuario -d postgres
```

#### 5.2 Criar Banco de Dados
```sql
CREATE DATABASE aracannabis_prod 
    WITH ENCODING 'UTF8' 
    LC_COLLATE='pt_BR.UTF-8' 
    LC_CTYPE='pt_BR.UTF-8';
```

#### 5.3 Verificar Conexão
```python
# test_db_connection.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print("✅ Conexão com PostgreSQL bem-sucedida!")
    conn.close()
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
```

## Próximos Passos

1. **Obter credenciais do PostgreSQL da Hostinger**
2. **Testar conexão com o banco**
3. **Criar versão condicional do frontend**
4. **Preparar arquivos de deploy**
5. **Executar deploy em ambiente de teste**
6. **Deploy em produção**

## Observações Importantes

- **Manter duas versões**: Uma com IA (desenvolvimento) e uma sem IA (produção básica)
- **Segurança**: Gerar novas chaves secretas para produção
- **Backup**: Sempre fazer backup antes de deploy
- **Monitoramento**: Configurar logs e monitoramento
- **LGPD**: Verificar conformidade em produção
