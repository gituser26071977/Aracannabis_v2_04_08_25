# Resumo das Correções para Deploy Docker/VPS

## ✅ Correções Realizadas

### 1. Padronização de Portas
**Arquivos modificados:**
- `Dockerfile.backend` - Alterado EXPOSE e CMD para porta 5002
- `entrypoint_siap.sh` - Alterado para porta 5002

### 2. Novos Scripts Criados
**`init_docker.py`** - Inicialização completa:
- Aguarda banco de dados ficar disponível
- Cria tabelas automaticamente
- Verifica superadmin

**`healthcheck.py`** - Verificação de saúde:
- Testa conexão com banco
- Verifica tabelas principais

### 3. Script de Deploy Melhorado
**`deploy_docker_vps.sh`** - Agora com:
- Validação de variáveis obrigatórias
- Aguardo saudável do banco
- Inicialização automática
- Health check pós-deploy

### 4. Correção de Tipo de Dados
**`models_extra.py`**:
- Alterado `associacao_id` de Integer para String(36) para compatibilidade com UUID

---

## ⚠️ Inconsistências Detectadas (Requer Atenção)

### Conflito de Schema: `associacoes.id`
Há duas definições conflitantes para a tabela `associacoes`:

1. **`saas_v1_init.sql`**: Usa `UUID` (tipo recomendado para SaaS)
2. **`association/models.py`**: Usa `Integer` (tipo antigo)

**Impacto:** Pode causar erro ao criar as tabelas se ambos forem executados.

**Recomendação:** Decidir qual schema usar e padronizar.

### Tabelas que Usam `associacao_id`:
- `pacientes` (UUID - do SQL)
- `usuarios_associacoes` (String(36) - corrigido)
- `membros_associacao` (Integer - do models.py)
- `estoque_associacao` (Integer - do models.py)
- `dispensacoes` (Integer - do models.py)

---

## 🚀 Como Fazer o Deploy

### 1. Preparar o Ambiente
```bash
# Copiar e configurar variáveis de ambiente
cp .env.production.example .env.production
nano .env.production  # Preencher todas as variáveis
```

### 2. Verificar Configurações Obrigatórias
```bash
# POSTGRES_PASSWORD - deve ser senha forte
# SECRET_KEY - deve ser chave única e segura
# GOOGLE_API_KEY - necessária para IA funcionar
```

### 3. Executar Deploy
```bash
chmod +x deploy_docker_vps.sh
./deploy_docker_vps.sh
```

### 4. Criar Superadmin (se necessário)
```bash
docker-compose -f docker-compose.prod.yml exec siap-backend python create_superadmin_simple.py
```

---

## 🔧 Comandos de Manutenção

### Ver Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f [serviço]
```

### Reiniciar
```bash
docker-compose -f docker-compose.prod.yml restart [serviço]
```

### Acessar Banco
```bash
docker-compose -f docker-compose.prod.yml exec siap-db psql -U siap_user -d aracannabis
```

### Backup do Banco
```bash
docker exec siap-db pg_dump -U siap_user aracannabis > backup_$(date +%Y%m%d).sql
```

---

## 📋 Checklist Pós-Deploy

- [ ] Backend responde em `/api/status`
- [ ] Frontend carrega sem erros
- [ ] Login funciona
- [ ] Banco de dados inicializado
- [ ] Superadmin criado
- [ ] APIs de IA configuradas (opcional)

---

## 🐛 Troubleshooting

### Erro: "port already allocated"
```bash
# Verificar processos usando porta 5002
sudo lsof -i :5002
# Matar processo ou alterar porta
```

### Erro: "database does not exist"
```bash
# Recriar banco
docker-compose -f docker-compose.prod.yml down -v  # CUIDADO: apaga dados!
docker-compose -f docker-compose.prod.yml up -d
```

### Erro: "relation X does not exist"
```bash
# Tabelas não criadas - executar manualmente
docker-compose -f docker-compose.prod.yml exec siap-backend python init_docker.py
```

### Erro de permissão denied
```bash
chmod +x *.sh
```

---

## 📊 Estrutura dos Serviços

```
┌─────────────────────────────────────────────────────────┐
│                      VPS Hostinger                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  siap-db     │  │siap-backend  │  │siap-frontend │  │
│  │  (postgres)  │  │  (flask)     │  │  (react)     │  │
│  │  porta:5440  │  │  porta:5002  │  │  porta:80    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │          │
│         └─────────────────┼─────────────────┘          │
│                           │                            │
│                    ┌──────┴──────┐                     │
│                    │  Traefik    │                     │
│                    │  (reverse)  │                     │
│                    └──────┬──────┘                     │
│                           │                            │
│                    ┌──────┴──────┐                     │
│                    │   Internet  │                     │
│                    └─────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📞 URLs de Acesso

| Ambiente | URL |
|----------|-----|
| Produção | https://aracannabis.com.br |
| API | https://api.aracannabis.com.br |
| Status | https://api.aracannabis.com.br/api/status |
