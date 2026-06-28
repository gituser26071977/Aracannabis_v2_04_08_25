# DEPLOY READINESS — FASE 4 (P0-A)

**Data:** 2026-06-22
**Escopo:** Auditoria final de deploy da FASE 4 + FASE 4.1 antes da publicação em produção.
**Branch:** `feat/clinica-management`
**Método:** somente leitura, baseado em evidência.

---

## 1. INVENTÁRIO DE MUDANÇAS (FASE 4.0 + FASE 4.1)

### 1.1 Arquivos novos

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `services/webhook_auth.py` | ~330 | Helper centralizado: HMAC SHA256, validate_timestamp, check_replay, register_webhook_event, decorators, startup check |

### 1.2 Arquivos modificados (FASE 4.0)

| Arquivo | Mudança |
|---------|---------|
| `.env.example` | +6 env vars (seção 11) |
| `app_cors_livre.py` | +`assert_required_secrets_on_startup` no `create_app()` |
| `routes/anamneses.py` | W3 + W3-adjacent endurecido com `validate_internal_key` |
| `routes/dr_anderson_webhook.py` | W3 `@internal_key_required` + W4 `@hmac_webhook_required` + TODO P1-LGPD |
| `routes/dynamic_tenant_webhook.py` | W2 `@hmac_webhook_required` + replay |
| `routes/mercadopago.py` | W1 `@mercadopago_webhook_required` (padrão oficial MP) + replay |
| `routes/modulos.py` | W5 `@hmac_webhook_required` + `simulate` gateado por `ALLOW_WEBHOOK_SIMULATION` |

### 1.3 Arquivos modificados (FASE 4.1)

| Arquivo | Mudança |
|---------|---------|
| `services/webhook_auth.py` | +`register_webhook_event()` (INSERT atômico + UNIQUE + IntegrityError) |
| `services/webhook_handler.py` | `webhook_handler.process()` usa `register_webhook_event` (elimina race) |
| `routes/mercadopago.py` | `check_replay` → `register_webhook_event` |
| `routes/dynamic_tenant_webhook.py` | idem |
| `routes/dr_anderson_webhook.py` | idem |
| `routes/modulos.py` | idem + **409 → 200 idempotente** |

### 1.4 Total

```
14 arquivos modificados, 275 insertions(+), 86 deletions(-)
1 arquivo novo (services/webhook_auth.py)
+ tests/smoke/test_webhook_security.py
+ docs/WEBHOOK_*.md
```

**Nenhuma alteração em frontend, models.py, ou contratos públicos de API.**

---

## 2. VARIÁVEIS DE AMBIENTE OBRIGATÓRIAS

### 2.1 Env vars novas da FASE 4 (6 vars)

| Var | Uso | Onde | Obrigatório em prod |
|-----|-----|------|---------------------|
| `MERCADOPAGO_WEBHOOK_SECRET` | W1 HMAC | `.env.example:122` | ✅ SIM |
| `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` | W5 HMAC | `.env.example:123` | ✅ SIM |
| `EVOLUTION_WEBHOOK_SECRET` | W2 HMAC | `.env.example:124` | ✅ SIM |
| `DR_ANDERSON_WEBHOOK_SECRET` | W4 HMAC | `.env.example:125` | ✅ SIM |
| `INTERNAL_SERVICE_KEY` | W3 + anamneses | `.env.example:128` | ✅ SIM |
| `ALLOW_WEBHOOK_SIMULATION` | Gate `simulate=true` em W5 | `.env.example:131` | ❌ só dev |

### 2.2 Geração dos secrets

```bash
# Para cada um dos 5 secrets
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.3 Cobertura em `scripts/validate_env.py`

⚠️ **Achado:** `scripts/validate_env.py` cobre apenas `WEBHOOK_SECRET_KEY` (legado) e `JWT_SECRET_KEY` / `SECRET_KEY`. **NÃO cobre as 5 env vars novas da FASE 4.**

**Impacto:** Operador que rodar `validate_env.py` antes do deploy **NÃO será alertado** sobre os 5 secrets faltando. Mas `assert_required_secrets_on_startup()` em `app_cors_livre.py:33-42` aborta o startup do gunicorn, então a falha é detectada imediatamente.

**Recomendação P1:** adicionar as 5 vars a `scripts/validate_env.py` em `REQUIRED_PRODUCTION_VARS`.

---

## 3. COMPATIBILIDADE COM docker-compose.prod.yml

### 3.1 Stack atual

**`docker-compose.prod.yml:43-93`** — container `siap-backend`:

```yaml
siap-backend:
  build:
    context: .
    dockerfile: Dockerfile.backend
  env_file:
    - .env.production
  environment:
    - FLASK_ENV=production
    - DATABASE_URL=postgresql://...
    ...
  command: [ "gunicorn", "--bind", "0.0.0.0:5002", "--timeout", "300",
             "--workers", "3", "--threads", "2", "app_cors_livre:create_app()" ]
```

### 3.2 Verificações

| Item | Status | Evidência |
|------|--------|-----------|
| `FLASK_ENV=production` setado | ✅ | linha 52 |
| `gunicorn` com `app_cors_livre:create_app()` | ✅ | linha 93 |
| Migrations aplicadas automaticamente | ✅ | `entrypoint_siap.sh:13` → `flask db upgrade` |
| `DATABASE_URL` para PostgreSQL | ✅ | linha 53 |
| `env_file: .env.production` | ✅ | linha 49-50 |
| `.env.production` presente no repo | ❌ | Não trackeado (correto — é gitignored) |

### 3.3 Risco de incompatibilidade

**Nenhum detectado.** FASE 4 + FASE 4.1 são compatíveis com `gunicorn` + `app_cors_livre:create_app()`.

⚠️ **Detalhe:** `Dockerfile.backend:33` usa `python app_cors_livre.py --port 5002`, mas é **sobrescrito** por `docker-compose.prod.yml:93` (gunicorn). Para garantir, operador deve usar **docker-compose.prod.yml**, não o Dockerfile sozinho.

---

## 4. COMPATIBILIDADE COM SYSTEMD

### 4.1 Service atual: `araos.service`

```ini
[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/araos/backend
Environment="PATH=/var/www/araos/backend/venv/bin"
ExecStart=/var/www/araos/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:create_app()
Restart=on-failure
```

### 4.2 Inconsistências detectadas

| Item | Status | Detalhes |
|------|--------|----------|
| Módulo `app` vs `app_cors_livre` | ⚠️ DIVERGÊNCIA | Service usa `app:create_app()`, projeto usa `app_cors_livre.py` |
| Path `/var/www/araos/backend` | ⚠️ Específico | Não usado em produção (que usa Docker) |
| Workers 3, bind 127.0.0.1:5000 | OK | Compatível com a app real |

### 4.3 Recomendação

⚠️ **Service systemd está INCONSISTENTE com o módulo real (`app_cors_livre`)**. Se o operador tentar usar `araos.service` em ambiente não-Docker (ex: fallback bare-metal), vai falhar com `ModuleNotFoundError: No module named 'app'`.

**NÃO bloqueia deploy** porque produção usa Docker + gunicorn (não systemd). Service está órfão / desatualizado.

**Recomendação P1:** atualizar `araos.service` para `app_cors_livre:create_app()` ou marcar como deprecated.

---

## 5. COMPATIBILIDADE COM EVOLUTION API

### 5.1 Padrão esperado (FASE 4)

- **Header:** `x-webhook-signature: sha256=<hex>`
- **Algoritmo:** HMAC SHA256 do body cru
- **Exemplo Evolution:** configuração via `webhook.set` com `headers: {"X-Webhook-Signature": "sha256=<hmac>"}`

**Helper:** `services/webhook_auth.py:129-160` (`validate_generic_hmac_signature`)

### 5.2 Documentação atual

⚠️ **Achado:** `docs/WHATSAPP_SETUP.md:33-50` documenta Evolution API enviando header **`X-Webhook-Secret`** (legado, sem HMAC).

**Esta documentação está DESATUALIZADA** — não reflete a FASE 4.

**Risco:** Operador que seguir o guia antigo vai configurar Evolution API com header errado → todos os webhooks Evolution (W2 + W4) vão falhar com 401.

**Ação do operador:** ao configurar Evolution, usar:
```bash
curl -X POST http://evolution-api:8080/webhook/set/<instance> \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.visualsmartflow.com.br/api/tenant/webhook",
    "events": ["messages.upsert"],
    "webhook_by_events": false,
    "headers": {
      "x-webhook-signature": "sha256={{hmac}}"
    }
  }'
```

⚠️ **NOTA IMPORTANTE:** A Evolution API **NÃO calcula HMAC automaticamente**. O operador precisa:
1. Calcular HMAC SHA256 do body em algum proxy/intermediário, OU
2. Configurar Evolution API para enviar o body puro e calcular HMAC no SIAP (mas isso requer que Evolution envie o body sem assinar — não protege nada)

**Solução realistica:** configurar Evolution API para enviar header fixo `X-Internal-Token` E o SIAP valida esse token via `compare_digest` (em vez de HMAC). Isso é mais simples e ainda elimina 100% dos ataques externos.

**Recomendação:** revisar o modelo de autenticação Evolution com o operador. Se Evolution API realmente não suporta HMAC nativo, considerar fallback para `X-Internal-Token` com `compare_digest`.

### 5.3 Compatibilidade com SIAP backend

- ✅ Endpoint `POST /api/tenant/webhook` aceita `x-webhook-signature`
- ✅ Endpoint `POST /api/dr-anderson/webhook` aceita `x-webhook-signature`
- ✅ Helper `validate_generic_hmac_signature` em `services/webhook_auth.py`
- ✅ Decorator `@hmac_webhook_required` aplicado em ambos

---

## 6. COMPATIBILIDADE COM MERCADO PAGO

### 6.1 Padrão esperado (FASE 4)

- **Headers:** `x-signature: ts=<timestamp>,v1=<hex_hmac>` + `x-request-id`
- **Template:** `id:{data_id};request-id:{x_request_id};ts:{ts};`
- **Algoritmo:** HMAC SHA256

**Helper:** `services/webhook_auth.py:78-123` (`validate_mercadopago_signature`)

### 6.2 Verificação contra doc oficial

**Fonte:** [Mercado Pago Developers — Webhooks](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks)

| Item | Doc MP | FASE 4 | Compatível? |
|------|--------|--------|-------------|
| Header `x-signature` | `ts=<timestamp>,v1=<hex>` | `services/webhook_auth.py:220` | ✅ |
| Header `x-request-id` | Referenciado em SDK | `services/webhook_auth.py:221` | ✅ |
| Template HMAC | `id:[data.id];request-id:[x-request-id];ts:[timestamp];` | `services/webhook_auth.py:117` | ✅ |
| HMAC SHA256 | Sim | Sim | ✅ |

### 6.3 Risco: dois webhooks MP, um secret no painel

⚠️ **Achado:** Painel MP aceita **UM secret por aplicação**, não por URL.

- W1 usa `MERCADOPAGO_WEBHOOK_SECRET`
- W5 usa `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` (secret diferente)

**Cenário A:** Operador provisiona **mesmo secret** em ambos `.env` → ambos webhooks funcionam. ✅

**Cenário B:** Operador provisiona **dois secrets diferentes** no MP → todas as notificações falham com 401. ❌

**Recomendação crítica para deploy runbook:** `MERCADOPAGO_WEBHOOK_SECRET` e `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` devem ser **o mesmo valor** (ou MP envia com secret A e SIAP valida com B → falha total).

### 6.4 Migração da integração atual

`services/mercadopago_service.py:19` JÁ lia `MERCADOPAGO_WEBHOOK_SECRET` antes da FASE 4, mas não validava assinatura. Comportamento preservado + validação adicionada.

**Risco de migração:** se MP começar a enviar webhook imediatamente após provisionar o secret, e a Evolution API estiver mal configurada (cenário B acima), todas as notificações falham → perda de pagamentos durante a janela de configuração.

**Recomendação:** provisionar secrets ANTES de deployar código. Janela de mudança: alguns minutos.

---

## 7. PROCESSO DE ROLLBACK

### 7.1 Cenário A — Rollback total da FASE 4

```bash
# 1. Reverter código
git revert <commit-fase4>

# 2. Reconstruir imagem Docker
docker compose -f docker-compose.prod.yml build siap-backend

# 3. Reiniciar container
docker compose -f docker-compose.prod.yml up -d siap-backend

# 4. (Opcional) Remover env vars do .env.production
# (não obrigatório — variáveis não usadas são ignoradas pelo código antigo)
```

**Tempo estimado:** 5-10 minutos
**Risco:** zero se MP não estiver enviando webhooks durante a janela
**Downtime:** 30 segundos (restart do container)

### 7.2 Cenário B — Rollback parcial (manter FASE 4 mas desabilitar HMAC em 1 webhook)

Não implementado. FASE 4 não tem feature flag de bypass.

**Workaround de emergência:** setar a env var do webhook específico com valor placeholder:
```bash
MERCADOPAGO_WEBHOOK_SECRET=disabled  # Aceita qualquer assinatura (NÃO recomendado)
```

⚠️ **Não usar** em produção — apenas debug temporário.

### 7.3 Cenário C — Rollback via Bypass Total

Se a aplicação não sobe em produção (startup check falha), operador pode:
```bash
# Temporariamente desabilitar startup check (NÃO recomendado)
FLASK_ENV=development  # bypass assert_required_secrets_on_startup
docker compose -f docker-compose.prod.yml up -d siap-backend
```

**Risco:** alto — todos os 5 webhooks ficam SEM autenticação. Usar apenas como último recurso.

### 7.4 Backup de estado anterior

```bash
# Antes do deploy, fazer backup do banco (webhook_logs é usado pela FASE 4.1)
docker exec siap-db pg_dump -U siap_user -d aracannabis > backup_pre_fase4.sql

# Backup do .env.production (manter versão antiga)
cp .env.production .env.production.bak
```

---

## 8. CHECKLIST OPERACIONAL — RESUMO

### 8.1 Antes do deploy (operador)

- [ ] Provisionar 5 secrets:
  - [ ] `MERCADOPAGO_WEBHOOK_SECRET`
  - [ ] `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` (mesmo valor que o anterior — CRÍTICO)
  - [ ] `EVOLUTION_WEBHOOK_SECRET`
  - [ ] `DR_ANDERSON_WEBHOOK_SECRET`
  - [ ] `INTERNAL_SERVICE_KEY`
- [ ] Adicionar 5 secrets ao `.env.production` no VPS
- [ ] Configurar painel MP com mesmo secret de W1 e W5
- [ ] Configurar Evolution API para enviar `x-webhook-signature: sha256=<hmac>`
- [ ] Backup do banco (pg_dump)
- [ ] Backup do `.env.production` (`.env.production.bak`)

### 8.2 Deploy

- [ ] Pull branch `feat/clinica-management` no VPS
- [ ] `git pull origin feat/clinica-management`
- [ ] `docker compose -f docker-compose.prod.yml build siap-backend`
- [ ] `docker compose -f docker-compose.prod.yml up -d siap-backend`
- [ ] Verificar logs: `docker logs -f siap-backend`

### 8.3 Pós-deploy (verificações)

- [ ] App subiu sem `RuntimeError` (startup check passou)
- [ ] `curl https://api.visualsmartflow.com.br/api/status` retorna 200
- [ ] `curl -X POST https://api.visualsmartflow.com.br/api/mercadopago/webhook` (sem signature) retorna **401** (não 400)
- [ ] `curl -X POST https://api.visualsmartflow.com.br/api/modulos/webhook` (sem signature) retorna **401**
- [ ] `curl -X POST https://api.visualsmartflow.com.br/api/tenant/webhook` (sem signature) retorna **401**
- [ ] `curl -X POST https://api.visualsmartflow.com.br/api/dr-anderson/criar-lead` (sem internal-key) retorna **401**

### 8.4 Smoke test em produção

- [ ] Enviar webhook MP com signature válida (gerar com `hmac.new`) → 200
- [ ] Reenviar mesmo webhook MP → 200 idempotente
- [ ] Enviar webhook Evolution com signature válida → 200
- [ ] Reenviar mesmo webhook Evolution → 200 idempotente
- [ ] Verificar tabela `webhook_logs`: linhas presentes, sem duplicatas

### 8.5 Rollback (se necessário)

- [ ] `git revert <commit-fase4>`
- [ ] `docker compose -f docker-compose.prod.yml build siap-backend`
- [ ] `docker compose -f docker-compose.prod.yml up -d siap-backend`
- [ ] Restaurar `.env.production` do `.env.production.bak` (se rollback completo das vars)

---

## 9. ACHADOS DA AUDITORIA

### 9.1 Bloqueadores técnicos

**ZERO.** Nenhum bloqueador técnico impede o deploy da FASE 4 + FASE 4.1.

### 9.2 Achados não-bloqueantes

| # | Severidade | Achado | Recomendação |
|---|-----------|--------|--------------|
| A1 | MÉDIO | `scripts/validate_env.py` não cobre as 5 env vars novas | Adicionar em P1 |
| A2 | MÉDIO | `docs/WHATSAPP_SETUP.md:33-50` documenta header antigo `X-Webhook-Secret` | Atualizar doc em P1 |
| A3 | ALTO | Evolution API não calcula HMAC automaticamente | Revisar modelo auth (considerar X-Internal-Token) |
| A4 | ALTO | Dois webhooks MP com secrets diferentes no painel | Garantir mesmo secret; documentar em runbook |
| A5 | BAIXO | `araos.service` systemd usa módulo errado (`app` em vez de `app_cors_livre`) | Corrigir em P1 ou marcar deprecated |
| A6 | BAIXO | Detector de produção divergente (config.py lê `ENVIRONMENT`, docker seta `FLASK_ENV`) | Pré-existente, fora escopo FASE 4 |
| A7 | BAIXO | `Dockerfile.backend` CMD é sobrescrito por docker-compose.prod.yml | Não é problema, apenas documentar |

### 9.3 Migration pendente

**ZERO.** Tabela `webhook_logs` já foi criada pela migration `REDACTED.py` (2026-06-07). Nenhuma migration adicional necessária para FASE 4 + FASE 4.1.

---

## 10. 5 RESPOSTAS FINAIS

### Q1. Existe algum bloqueador técnico para deploy?
**NÃO.** Aplicação sobe com `gunicorn`, migrations já estão aplicadas, helpers são compatíveis, smoke test local passou em 10/10 testes. Único cuidado: provisionar secrets ANTES de fazer deploy (não depois).

### Q2. Existe alguma migration pendente?
**NÃO.** Tabela `webhook_logs` já existe (migration `a1b2c3d4e5f6` aplicada em 2026-06-07). UNIQUE constraint já está presente (`models_extra.py:138-140`).

### Q3. Existe alguma variável de ambiente faltando?
**SIM** — para deploy em produção, 5 vars precisam ser adicionadas ao `.env.production`:
- `MERCADOPAGO_WEBHOOK_SECRET`
- `MERCADOPAGO_MODULOS_WEBHOOK_SECRET`
- `EVOLUTION_WEBHOOK_SECRET`
- `DR_ANDERSON_WEBHOOK_SECRET`
- `INTERNAL_SERVICE_KEY`

Se faltar qualquer uma, `assert_required_secrets_on_startup()` em `app_cors_livre.py:33-42` aborta o startup com `RuntimeError` claro.

### Q4. Existe alguma incompatibilidade com produção?
**SIM — 2 incompatibilidades potenciais:**

1. **MercadoPago (ALTO):** W1 e W5 usam secrets diferentes. Se operador provisionar DOIS secrets no painel MP (um por webhook), todas as notificações falham. **Mitigação:** usar MESMO secret para ambos.

2. **Evolution API (ALTO):** Evolution não calcula HMAC nativamente. Operador precisa configurar um proxy intermediário para calcular HMAC. Alternativa: usar `X-Internal-Token` com `compare_digest` (mais simples, igualmente seguro).

### Q5. Você aprova o deploy da FASE 4 em produção?
**APROVAÇÃO CONDICIONAL — após 3 ações do operador:**

1. ✅ Provisionar 5 secrets no `.env.production` E no painel MP/Evolução (mesmo secret para W1+W5 no MP)
2. ✅ Atualizar configuração Evolution API para suportar HMAC (ou fallback `X-Internal-Token`)
3. ✅ Atualizar `docs/WHATSAPP_SETUP.md` para refletir o novo padrão `x-webhook-signature` (recomendado para próximos deployments)

**Após essas 3 ações:** ✅ **APROVAR deploy da FASE 4 + FASE 4.1 em produção.**

---

## 11. PRÓXIMOS PASSOS

1. ✅ Aguardar revisão humana deste relatório
2. ⏸️ Operador: provisionar secrets ANTES do deploy
3. ⏸️ Operador: deploy em `api.visualsmartflow.com.br`
4. ⏸️ Operador: smoke test em produção (verificar 401 sem signature + 200 com signature válida)
5. ⏸️ Iniciar FASE 5 (Rate Limit Redis) **somente após aprovação humana**

---

**⚠️ Parando aqui. NÃO iniciar FASE 5. NÃO criar novas funcionalidades. Aguardando revisão humana.**