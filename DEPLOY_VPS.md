# Deploy VPS - Aracannabis SIAP

## Correções Realizadas

### 1. Portas Padronizadas (🔧 Corrigido)
- **Problema**: Inconsistência nas portas (5002 vs 5004 vs 3000)
- **Solução**: Padronizada porta **5002** em todos os arquivos:
  - `Dockerfile.backend` - EXPOSE 5002
  - `Dockerfile.backend` - CMD na porta 5002
  - `entrypoint_siap.sh` - porta 5002

### 2. Script de Inicialização (🆕 Criado)
- **`init_docker.py`**: Script completo de inicialização que:
  - Aguarda o banco de dados ficar disponível
  - Cria as tabelas automaticamente
  - Verifica se há superadmin configurado

### 3. Healthcheck (🆕 Criado)
- **`healthcheck.py`**: Verifica saúde do sistema:
  - Conexão com banco de dados
  - Tabelas principais existem

### 4. Script de Deploy Atualizado (🔧 Melhorado)
- **`deploy_docker_vps.sh`**: Agora com:
  - Validação de variáveis de ambiente
  - Aguardo do banco de dados
  - Inicialização automática
  - Health check pós-deploy

## Checklist Pré-Deploy

### 1. Configurar `.env.production`
```bash
cp .env.production.example .env.production
# Editar .env.production com valores reais:
# - POSTGRES_PASSWORD (senha forte!)
# - SECRET_KEY (chave secreta única!)
# - GOOGLE_API_KEY (para IA funcionar)
# - MARITACA_API_KEY (opcional)
```

### 2. Verificar Rede Traefik
```bash
docker network create web  # Se ainda não existir
```

### 3. Executar Deploy
```bash
chmod +x deploy_docker_vps.sh
./deploy_docker_vps.sh
```

## Comandos Úteis

### Ver Logs
```bash
# Todos os serviços
docker-compose -f docker-compose.prod.yml logs -f

# Backend específico
docker-compose -f docker-compose.prod.yml logs -f siap-backend

# Banco de dados
docker-compose -f docker-compose.prod.yml logs -f siap-db
```

### Reiniciar Serviços
```bash
# Reiniciar tudo
docker-compose -f docker-compose.prod.yml restart

# Reiniciar apenas backend
docker-compose -f docker-compose.prod.yml restart siap-backend
```

### Acessar Containers
```bash
# Shell no backend
docker-compose -f docker-compose.prod.yml exec siap-backend bash

# Shell no banco
docker-compose -f docker-compose.prod.yml exec siap-db psql -U siap_user -d aracannabis
```

### Criar Superadmin
```bash
docker-compose -f docker-compose.prod.yml exec siap-backend python create_superadmin_simple.py
```

### Health Check
```bash
docker-compose -f docker-compose.prod.yml exec siap-backend python healthcheck.py
```

## URLs Importantes

| Serviço | URL |
|---------|-----|
| Frontend | https://aracannabis.com.br |
| API | https://api.aracannabis.com.br |
| API Status | https://api.aracannabis.com.br/api/status |

## Troubleshooting

### Banco de dados não conecta
```bash
# Verificar se o container está rodando
docker-compose -f docker-compose.prod.yml ps

# Verificar logs do DB
docker-compose -f docker-compose.prod.yml logs siap-db

# Testar conexão manual
docker-compose -f docker-compose.prod.yml exec siap-db pg_isready -U siap_user
```

### Backend não inicia
```bash
# Verificar erros de importação
docker-compose -f docker-compose.prod.yml logs siap-backend | head -100

# Testar healthcheck
docker-compose -f docker-compose.prod.yml exec siap-backend python healthcheck.py
```

### Erro de permissão
```bash
# Fixar permissões dos scripts
chmod +x deploy_docker_vps.sh entrypoint_siap.sh
```

## Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `POSTGRES_PASSWORD` | Senha do banco | `senha_forte_123` |
| `SECRET_KEY` | Chave Flask | `chave_aleatoria_32_chars` |
| `GOOGLE_API_KEY` | API Google AI | `AIza...` |
| `JWT_SECRET_KEY` | Chave JWT | `outra_chave_secreta` |
