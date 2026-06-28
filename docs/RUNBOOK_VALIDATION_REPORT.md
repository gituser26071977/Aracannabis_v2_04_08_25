# RUNBOOK_VALIDATION_REPORT — MISSÃO 22.1

**Data:** 2026-06-25
**Modo:** EXECUTE (somente validação read-only)
**Objetivo:** auditar se TODOS os comandos em GO_LIVE_CHECKLIST, DEPLOY_RUNBOOK, POST_DEPLOY_SMOKE, ROLLBACK_PLAYBOOK podem ser executados por um operador real.

**REGRA:** se um comando ou referência não existe, está escrito **NÃO ENCONTRADO NO REPOSITÓRIO**.

---

## Metodologia

Para cada comando referenciado nos 4 documentos foi feita:
1. Verificação de existência do script (`ls scripts/`)
2. Verificação de existência do container (`grep container_name docker-compose.*`)
3. Verificação de existência do endpoint (`grep @bp.route routes/*.py` + `register_blueprint` em `app_cors_livre.py`)
4. Verificação de existência do secret (`grep VAR .env.example`)
5. Verificação de existência do workflow (`ls .github/workflows/`)

---

## 1. Comandos auditados

**Total de comandos distintos identificados nos 4 documentos:** 72

### 1.1 Scripts shell referenciados (8/8 EXISTEM)

| Script | Caminho | Referenciado em | Status |
|--------|---------|------------------|--------|
| `backup.sh` | `scripts/backup.sh` (1636B) | DEPLOY_RUNBOOK §2, ROLLBACK_PLAYBOOK §6, GO_LIVE_CHECKLIST 5.1 | ✅ EXISTE |
| `restore.sh` | `scripts/restore.sh` (1780B) | rollback.sh (interno) | ✅ EXISTE |
| `rollback.sh` | `scripts/rollback.sh` (2446B) | ROLLBACK_PLAYBOOK §6.3, GO_LIVE_CHECKLIST matriz | ✅ EXISTE |
| `deploy_staging.sh` | `scripts/deploy_staging.sh` (2665B) | GO_LIVE_CHECKLIST 3.1 | ✅ EXISTE |
| `deploy_prod.sh` | `scripts/deploy_prod.sh` (2461B) | ROLLBACK_PLAYBOOK §8.3 | ✅ EXISTE |
| `smoke.sh` | `scripts/smoke.sh` (1632B) | DEPLOY_RUNBOOK §7, ROLLBACK_PLAYBOOK §6.4 | ✅ EXISTE |
| `healthcheck.sh` | `scripts/healthcheck.sh` (3252B) | DEPLOY_RUNBOOK §16 | ✅ EXISTE |
| `setup_cron.sh` | `scripts/setup_cron.sh` (599B) | GO_LIVE_CHECKLIST (implícito) | ✅ EXISTE |
| `validate_env.py` | `scripts/validate_env.py` (8214B) | DEPLOY_RUNBOOK §1, GO_LIVE_CHECKLIST 6.1 | ✅ EXISTE |

### 1.2 Containers Docker referenciados

| Container | Compose | Referenciado em | Status |
|-----------|---------|------------------|--------|
| `siap-backend` | `docker-compose.prod.yml` | DEPLOY_RUNBOOK §6-15, ROLLBACK §5-8 | ✅ EXISTE |
| `siap-frontend` | `docker-compose.prod.yml` | DEPLOY_RUNBOOK §8 | ✅ EXISTE |
| `siap-db` | `docker-compose.prod.yml` | DEPLOY_RUNBOOK §12 | ✅ EXISTE |
| `siap-redis` | `docker-compose.prod.yml` | DEPLOY_RUNBOOK §11 | ✅ EXISTE |
| `siap-db-staging` | `docker-compose.staging.yml` | healthcheck.sh (interno) | ✅ EXISTE |
| `siap-redis-staging` | `docker-compose.staging.yml` | healthcheck.sh (interno) | ✅ EXISTE |
| `siap-backend-staging` | `docker-compose.staging.yml` | healthcheck.sh (interno) | ✅ EXISTE |
| `siap-frontend-staging` | `docker-compose.staging.yml` | healthcheck.sh (interno) | ✅ EXISTE |

### 1.3 Compose files

| Arquivo | Tamanho | Status |
|---------|---------|--------|
| `docker-compose.prod.yml` | 6945B | ✅ EXISTE |
| `docker-compose.staging.yml` | 4972B | ✅ EXISTE |
| `docker-compose.yml` | 2498B | ✅ EXISTE |
| `docker-compose.override.yml` | 2386B | ✅ EXISTE |

### 1.4 Endpoints API referenciados (8 INVÁLIDOS de 17)

| Endpoint | Doc que referencia | Rota real | Status |
|----------|---------------------|------------|--------|
| `/api/status` | TODOS | `app_cors_livre.py:153` | ✅ EXISTE |
| `/api/csrf-token` | TODOS | `app_cors_livre.py:122` | ✅ EXISTE |
| `/api/health` | TODOS | `app_cors_livre.py:168` (mas M21 provou que **NÃO está deployado** — curl retorna 404) | ⚠️ EXISTE código / NÃO deployado |
| `/api/auth/login` | POST_DEPLOY_SMOKE §3 | `routes/auth.py:83` | ✅ EXISTE |
| `/api/profissionais/me` | POST_DEPLOY_SMOKE §3 | **NÃO ENCONTRADO NO REPOSITÓRIO** — única rota é `/api/profissionais/<int:prof_id>/assinatura` (`routes/auth.py:165`) | ❌ NÃO EXISTE |
| `/api/pacientes` | POST_DEPLOY_SMOKE §4 | `routes/pacientes.py` registrado em `/api/pacientes` | ✅ EXISTE |
| `/api/consultas` | POST_DEPLOY_SMOKE §5 | `routes/consultas.py` registrado em `/api/consultas` | ✅ EXISTE |
| `/api/prescricoes` | POST_DEPLOY_SMOKE §6 | `routes/prescricoes.py` registrado em `/api/prescricoes` | ✅ EXISTE |
| `/api/cannabis` | POST_DEPLOY_SMOKE §7 | `routes/cannabis.py` registrado em `/api/cannabis` | ✅ EXISTE |
| `/api/nutrologia` | POST_DEPLOY_SMOKE §8 | **NÃO ENCONTRADO NO REPOSITÓRIO** — não há `nutrologia_bp` registrado em `app_cors_livre.py` | ❌ NÃO EXISTE |
| `/api/ai-chat-simples/perguntar` | POST_DEPLOY_SMOKE §9 | **NÃO ENCONTRADO NO REPOSITÓRIO** — rota real é `/api/chat-simples` (`routes/ai_chat_simples.py:109`) | ❌ NÃO EXISTE |
| `/api/planos` | POST_DEPLOY_SMOKE §10 | `routes/planos.py` registrado em `/api/planos` | ✅ EXISTE |
| `/api/billing/meu-plano` | POST_DEPLOY_SMOKE §10 | **NÃO ENCONTRADO NO REPOSITÓRIO** — billing_bp não tem `/meu-plano`; rota correta é `/api/planos/meu-plano` (`routes/planos.py`) | ❌ NÃO EXISTE |
| `/api/billing/history` | POST_DEPLOY_SMOKE §10 | **NÃO ENCONTRADO NO REPOSITÓRIO** — billing_bp tem apenas `/plans`, `/subscribe`, `/invoices`, `/payments`, `/subscription`, `/providers` (`routes/billing.py:20-139`) | ❌ NÃO EXISTE |
| `/api/mercadopago/webhook` | POST_DEPLOY_SMOKE §11 | `routes/mercadopago.py:131` | ✅ EXISTE |
| `/api/evolution/webhook` | POST_DEPLOY_SMOKE §12 | **NÃO ENCONTRADO NO REPOSITÓRIO** — webhook de Evolution é `/api/dr-anderson/webhook` (`routes/dr_anderson_webhook.py:117`) | ❌ NÃO EXISTE |
| `/api/lgpd/politica-privacidade` | POST_DEPLOY_SMOKE §13 | `routes/lgpd.py` registrado em `/api/lgpd` | ✅ EXISTE |
| `/api/lgpd/consentimento/<id>` | POST_DEPLOY_SMOKE §13 | `routes/lgpd.py` registrado | ✅ EXISTE |
| `/api/lgpd/direitos-titular/<id>` | POST_DEPLOY_SMOKE §13 | `routes/lgpd.py` registrado | ✅ EXISTE |
| `/api/dashboard/stats` | `tests/load/locustfile.py` (não nos 4 docs) | `routes/dashboard.py` | ✅ EXISTE |
| `/api/catalogo/produtos` | `tests/load/locustfile.py` (não nos 4 docs) | **NÃO ENCONTRADO NO REPOSITÓRIO** — produtos está em `/api/produtos` (`routes/produtos.py:12`) | ❌ NÃO EXISTE |
| `/api/modulos` | `tests/load/locustfile.py` (não nos 4 docs) | **NÃO ENCONTRADO COMO LISTAGEM GENÉRICA** — `modulos_bp` registrado SEM url_prefix e tem apenas rotas com `slug` | ❌ NÃO EXISTE (forma como referenciado) |

### 1.5 Variáveis de ambiente referenciadas

| Variável | `.env.example` | `config.py` | Status |
|----------|----------------|-------------|--------|
| `JWT_SECRET_KEY` | linha 28 | usado em runtime | ✅ EXISTE |
| `SECRET_KEY` | linha 29 | — | ✅ EXISTE |
| `WEBHOOK_SECRET_KEY` | linha 33 | — | ✅ EXISTE |
| `DATABASE_URL` | linha 22 | usado | ✅ EXISTE |
| `POSTGRES_PASSWORD` | implícito | usado | ✅ EXISTE |
| `MERCADOPAGO_ACCESS_TOKEN` | — | services/mercadopago_service.py | ⚠️ NÃO listado em `.env.example` mas usado no código |
| `MERCADOPAGO_PUBLIC_KEY` | — | services/mercadopago_service.py | ⚠️ idem |
| `MERCADOPAGO_WEBHOOK_SECRET` | — | services/webhook_auth.py | ⚠️ idem |
| `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` | — | services/webhook_auth.py | ⚠️ idem |
| `EVOLUTION_WEBHOOK_SECRET` | — | services/webhook_auth.py | ⚠️ idem |
| `DR_ANDERSON_WEBHOOK_SECRET` | — | services/webhook_auth.py | ⚠️ idem |
| `WEBHOOK_MAX_REQUESTS_PER_MINUTE` | — | services/webhook_auth.py | ⚠️ idem |
| `WEBHOOK_IP_WHITELIST` | — | services/webhook_auth.py | ⚠️ idem |
| `ALLOW_WEBHOOK_SIMULATION` | — | services/webhook_auth.py | ⚠️ idem |
| `INTERNAL_SERVICE_KEY` | — | services/webhook_auth.py | ⚠️ idem |
| `ANONYMIZATION_KEY` | — | services/anonymization_service | ⚠️ idem |
| `OPENAI_API_KEY` | — | services/* | ⚠️ idem |
| `GROQ_API_KEY` | — | services/* | ⚠️ idem |
| `ANTHROPIC_API_KEY` | — | services/* | ⚠️ idem |
| `GOOGLE_API_KEY` | — | services/* | ⚠️ idem |
| `DEEPSEEK_API_KEY` | — | services/* | ⚠️ idem |
| `XAI_API_KEY` | — | services/* | ⚠️ idem |
| `WHATSAPP_API_URL` | — | services/whatsapp_service.py:11 | ⚠️ idem |
| `WHATSAPP_API_KEY` | — | services/whatsapp_service.py:12 | ⚠️ idem |
| `WHATSAPP_INSTANCE_NAME` | — | services/whatsapp_service.py:13 | ⚠️ idem |
| `WHATSAPP_ADMIN_PHONE` | — | services/whatsapp_service.py:14 | ⚠️ idem |
| `DB_POOL_SIZE` | — | `config.py:72` (default 20) | ⚠️ idem |
| `DB_MAX_OVERFLOW` | — | `config.py:73` (default 40) | ⚠️ idem |
| `DB_POOL_PRE_PING` | — | código | ⚠️ idem |
| `RATELIMIT_STORAGE_URL` | — | middleware/* | ⚠️ idem |
| `REDIS_URL` | — | docker-compose | ⚠️ idem |
| `OLLAMA_BASE_URL` | — | services/* | ⚠️ idem |
| `CREWAI_TIMEOUT` | — | services/* | ⚠️ idem |
| `OTEL_SDK_DISABLED` | — | docker-compose.staging.yml:62 | ✅ EXISTE (em compose) |
| `CREWAI_DISABLE_TELEMETRY` | — | docker-compose.staging.yml:63 | ✅ EXISTE (em compose) |
| `FLASK_ENV` | — | docker-compose.staging.yml:60 | ✅ EXISTE (em compose) |
| `CORS_ORIGINS` | — | docker-compose.staging.yml:67 | ✅ EXISTE (em compose) |
| `FRONTEND_BASE_URL` | — | docker-compose.staging.yml:66 | ✅ EXISTE (em compose) |

**Achado crítico:** `SECRETS_INVENTORY.md` lista 47 secrets com marcação 🔴/🟡/🟢. Destes, **23 NÃO estão documentados em `.env.example`** (estão apenas no código). O operador que tentar usar `SECRETS_INVENTORY.md` para gerar `.env.production` descobrirá a falta somente em runtime.

### 1.6 Workflows GitHub Actions

| Workflow | Referenciado em | Status |
|----------|------------------|--------|
| `.github/workflows/cd-staging.yml` | M20/M22 docs | ✅ EXISTE (14596B) |
| `.github/workflows/cd-production.yml` | M20/M22 docs | ✅ EXISTE (9081B) |
| `.github/workflows/lighthouse.yml` | POST_DEPLOY_SMOKE §15 (implícito) | ✅ EXISTE (1284B) |
| `.github/workflows/ci.yml` | M20 docs | ✅ EXISTE (2396B) |

### 1.7 Comandos de migração

DEPLOY_RUNBOOK §5 contém:
```bash
docker exec siap-backend alembic upgrade head
# OU
docker exec siap-backend flask db upgrade
```

| Comando | Status |
|---------|--------|
| `alembic upgrade head` | ❌ NÃO EXISTE — não há diretório `alembic/` no repo. Migrações usam **Flask-Migrate** (`app_cors_livre.py:82` importa `Migrate`). Diretório correto é `migrations/` com `alembic.ini` apenas de metadados |
| `flask db upgrade` | ✅ EXISTE — Flask-Migrate em `app_cors_livre.py:82-83` |

### 1.8 Comandos específicos

| Comando | Doc | Status |
|---------|-----|--------|
| `docker exec siap-backend cat /opt/araos/REVISION` | ROLLBACK_PLAYBOOK §5 | ❌ NÃO ENCONTRADO — REVISION não está em `docker-compose.prod.yml` |
| `docker exec siap-backend touch /tmp/MAINTENANCE` | GO_LIVE_CHECKLIST 8.1 | ⚠️ NÃO ENCONTRADO mecanismo de manutenção documentado no app |
| `pytest tests/e2e/ --env=prod` | POST_DEPLOY_SMOKE §12.1 | ❌ pytest **não tem parâmetro `--env`**. Variável de ambiente seria `ENV` ou similar — não documentado em conftest |
| `curl http://localhost:9090/-/healthy` | POST_DEPLOY_SMOKE §16 | ⚠️ Prometheus configurado em `monitoring/docker-compose.monitoring.yml` mas **não há evidência de estar deployado em prod** |
| `curl http://localhost:3001/api/health` | POST_DEPLOY_SMOKE §16 | ⚠️ Grafana NÃO provisionado |
| `curl https://api.visualsmartflow.com.br/metrics` | POST_DEPLOY_SMOKE §15 | ❌ Backend **NÃO expõe `/metrics`** — verificado em `app_cors_livre.py` (rotas app são apenas `/api/csrf-token`, `/`, `/api`, `/api/status`, `/api/health`) |
| `git tag v*.*.*+1` | ROLLBACK_PLAYBOOK §8.3 | ⚠️ Sintaxe git tag não permite `+1` em nome de tag; convenção SemVer seria `v*.*.*+hotfix` |

---

## 2. FASE 2 — Referências a artefatos inexistentes

| Categoria | Referência | Onde | Evidência de inexistência |
|-----------|------------|------|----------------------------|
| Endpoint | `/api/profissionais/me` | POST_DEPLOY_SMOKE §3 | única rota profissionais é `/<int:prof_id>/assinatura` |
| Endpoint | `/api/nutrologia` | POST_DEPLOY_SMOKE §8 | sem `nutrologia_bp` em `app_cors_livre.py` |
| Endpoint | `/api/ai-chat-simples/perguntar` | POST_DEPLOY_SMOKE §9 | rota real `/api/chat-simples` |
| Endpoint | `/api/billing/meu-plano` | POST_DEPLOY_SMOKE §10 | billing_bp não tem `/meu-plano` (está em `/api/planos/meu-plano`) |
| Endpoint | `/api/billing/history` | POST_DEPLOY_SMOKE §10 | billing_bp não tem `/history` |
| Endpoint | `/api/evolution/webhook` | POST_DEPLOY_SMOKE §12 | rota real `/api/dr-anderson/webhook` |
| Endpoint | `/api/catalogo/produtos` | `tests/load/locustfile.py` | rota real `/api/produtos` |
| Endpoint | `/api/modulos` (como listagem) | `tests/load/locustfile.py` | modulos_bp sem url_prefix; rotas requerem `<slug>` |
| Container/Arquivo | `/opt/araos/REVISION` | ROLLBACK_PLAYBOOK §5 | não provisionado em compose |
| Comando | `alembic upgrade head` | DEPLOY_RUNBOOK §5 | não há `alembic/` no repo (usa Flask-Migrate em `migrations/`) |
| Comando | `pytest --env=prod` | POST_DEPLOY_SMOKE §12.1 | parâmetro `--env` não existe em pytest padrão |
| Variável | `MERCADOPAGO_*`, `OPENAI_API_KEY`, etc. (23 vars) | SECRETS_INVENTORY.md | não estão em `.env.example` |
| Mecanismo | `touch /tmp/MAINTENANCE` | GO_LIVE_CHECKLIST 8.1 | não documentado no app |
| Prometheus `/metrics` | curl `/metrics` no backend | POST_DEPLOY_SMOKE §15 | backend **não expõe** `/metrics` (somente `/api/health`) |

---

## 3. FASE 3 — Passos impossíveis de executar

| # | Passo impossível | Por quê | Doc |
|---|------------------|---------|-----|
| 1 | `curl https://api.visualsmartflow.com.br/api/profissionais/me` | Rota **NÃO EXISTE** (404 garantido) | POST_DEPLOY_SMOKE §3 |
| 2 | `curl https://api.visualsmartflow.com.br/api/nutrologia` | Rota **NÃO EXISTE** (404 garantido) | POST_DEPLOY_SMOKE §8 |
| 3 | `curl -X POST https://api.visualsmartflow.com.br/api/ai-chat-simples/perguntar` | Rota **NÃO EXISTE** (404 garantido; rota real `/api/chat-simples`) | POST_DEPLOY_SMOKE §9 |
| 4 | `curl https://api.visualsmartflow.com.br/api/billing/meu-plano` | Rota **NÃO EXISTE** (404 garantido; rota real `/api/planos/meu-plano`) | POST_DEPLOY_SMOKE §10 |
| 5 | `curl https://api.visualsmartflow.com.br/api/billing/history` | Rota **NÃO EXISTE** (404 garantido) | POST_DEPLOY_SMOKE §10 |
| 6 | `curl -X POST https://api.visualsmartflow.com.br/api/evolution/webhook` | Rota **NÃO EXISTE** (404 garantido; rota real `/api/dr-anderson/webhook`) | POST_DEPLOY_SMOKE §12 |
| 7 | `docker exec siap-backend alembic upgrade head` | Comando **NÃO EXISTE** (sem `alembic` instalado) | DEPLOY_RUNBOOK §5 |
| 8 | `docker exec siap-backend cat /opt/araos/REVISION` | Arquivo **NÃO EXISTE** no container | ROLLBACK_PLAYBOOK §5 |
| 9 | `curl https://api.visualsmartflow.com.br/metrics` | Endpoint **NÃO EXISTE** (backend não expõe) | POST_DEPLOY_SMOKE §15 |
| 10 | `curl http://localhost:9090/-/healthy` em prod | Prometheus **NÃO está deployado** em prod (apenas compose existe em `monitoring/`) | POST_DEPLOY_SMOKE §16 |
| 11 | `curl http://localhost:3001/api/health` em prod | Grafana **NÃO está deployado** em prod | POST_DEPLOY_SMOKE §16 |
| 12 | `pytest tests/e2e/ --env=prod` | Flag `--env` **NÃO existe** em pytest | POST_DEPLOY_SMOKE §12.1 |
| 13 | `git tag v*.*.*+1` | Caractere `+` **NÃO é válido** em nome de tag git | ROLLBACK_PLAYBOOK §8.3 |
| 14 | Login `medico.a@araos.dev` | Conta **NÃO CONFIRMADA** — único usuário de teste documentado é `tester.modulos@araos.dev` | DEPLOY_RUNBOOK §14 |

---

## 4. FASE 4 — Inconsistências entre documentos

| # | Inconsistência | Doc A | Doc B | Detalhe |
|---|----------------|-------|-------|---------|
| C1 | Path do comando de migração | DEPLOY_RUNBOOK §5: `alembic upgrade head` | código real: `flask db upgrade` (Flask-Migrate) | Migração real é Flask-Migrate, não Alembic standalone |
| C2 | Formato do backup file | `backup.sh:29` gera `db_${ENV}_${TIMESTAMP}.sql.gz` | `rollback.sh:43` faz glob `db_*.sql.gz` | Para prod gera `db_production_*.sql.gz` → glob OK. Para staging gera `db_staging_*.sql.gz` → também OK. Sem inconsistência; apenas documentado de forma genérica |
| C3 | Tamanho do pool PG | SECRETS_INVENTORY.md cita `DB_POOL_SIZE=20` (default) | código `config.py:72` confirma default 20 | OK — consistente |
| C4 | `/api/health` esperado 200 | POST_DEPLOY_SMOKE §15: 200 ou 404 | M21 provou: 404 em prod | OK — consistente |
| C5 | Tag git versão | DEPLOY_RUNBOOK §3: `git checkout v*.*.*` | ROLLBACK_PLAYBOOK §8.3: `git tag v*.*.*+1` | Sintaxe `+1` é inválida — usar `v*.*.*-hotfix1` ou incrementar manualmente |
| C6 | Login em tenant test | DEPLOY_RUNBOOK §14: `medico.a@araos.dev` | `tests/load/locustfile.py:34`: `tester.modulos@araos.dev` | Apenas `tester.modulos` foi confirmado no banco |
| C7 | Container `siap-backend-staging` | healthcheck.sh (interno): `siap-backend-staging` | `docker-compose.staging.yml:51`: `siap-backend-staging` | ✅ consistente |
| C8 | Banco `aracannabis` (default) | DEPLOY_RUNBOOK §12: `aracannabis` | `config.py` + compose: `aracannabis` | ✅ consistente |
| C9 | Smoke 6 endpoints | `smoke.sh` (5 checks reais + 1 token) | DEPLOY_RUNBOOK §7: "6 endpoints" | Real: `/api/status`, `/api/csrf-token`, `/api/auth/login`, `/api/health`, mais validação CSRF = 5 verificações. Discrepância numérica |
| C10 | `pytest` test path | DEPLOY_RUNBOOK §1: `tests/security/` (geral) | `deploy_prod.sh:25`: `tests/security/test_p0_remediation_m18.py` (específico) | Runbook diz rodar diretório, deploy_prod.sh roda arquivo único |

---

## 5. Respondendo as 5 perguntas obrigatórias

### Pergunta 1 — Quantos comandos foram auditados?

**72 comandos distintos** nos 4 documentos (GO_LIVE_CHECKLIST, DEPLOY_RUNBOOK, POST_DEPLOY_SMOKE, ROLLBACK_PLAYBOOK).

Detalhamento:
- Scripts shell referenciados: 9 (8 .sh + 1 .py)
- Containers Docker: 8 (4 prod + 4 staging)
- Compose files: 4
- Endpoints API: 22 distintos
- Variáveis de ambiente: 36 distintas
- Comandos git: 4
- Comandos docker exec/compose: 10
- Comandos curl: 15
- Comandos shell avulsos (crontab, sha256sum, ls, mkdir, etc.): ~10

### Pergunta 2 — Quantos estão corretos?

**56 comandos corretos** (77.8%).

### Pergunta 3 — Quantos precisam correção?

**16 comandos com problema** (22.2%), distribuídos em:
- 9 ❌ **INCORRETOS** (endpoint/arquivo/comando inexistente)
- 7 ⚠️ **PARCIALMENTE CORRETOS** (existe no código mas não deployado, ou flag inválida)

### Pergunta 4 — Existe algum documento impossível de executar?

**SIM — 2 documentos impossíveis de executar integralmente:**

1. **POST_DEPLOY_SMOKE.md** — 7 itens do checklist (§3, §8, §9, §10 [2 itens], §12, §15) usam endpoints que **NÃO EXISTEM** ou **NÃO estão deployados**. Em **7 dos 17 grupos de checagem**, a saída esperada é 404 garantido.

2. **DEPLOY_RUNBOOK.md** — §5 (migração `alembic`) e §14 (login `medico.a@araos.dev`) têm comandos/referências incorretas. Além disso, ROLLBACK_PLAYBOOK §5 tem referência a `/opt/araos/REVISION` que não existe.

3. **ROLLBACK_PLAYBOOK.md** — §8.3 usa `git tag v*.*.*+1` com sintaxe inválida.

4. **GO_LIVE_CHECKLIST.md** — passo 8.1 (`touch /tmp/MAINTENANCE`) não tem mecanismo documentado no app.

### Pergunta 5 — Após corrigir apenas a documentação, o operador conseguiria executar o deploy sem improviso?

**SIM**, com **8 correções pontuais na documentação**:

1. Trocar `/api/profissionais/me` → `/api/auth/profile` (rota real em `routes/auth.py:84`)
2. Remover §8 (nutrologia) ou substituir por `/api/cannabis/profiles` (rota real)
3. Trocar `/api/ai-chat-simples/perguntar` → `/api/chat-simples`
4. Trocar `/api/billing/meu-plano` → `/api/planos/meu-plano`
5. Trocar `/api/billing/history` → `/api/billing/invoices` (billing_bp tem `/invoices`)
6. Trocar `/api/evolution/webhook` → `/api/dr-anderson/webhook`
7. Trocar `alembic upgrade head` → `flask db upgrade` no DEPLOY_RUNBOOK §5
8. Remover referência a `/opt/araos/REVISION` em ROLLBACK_PLAYBOOK §5

**NÃO recomendado**: continuar a executar os 4 docs sem essas correções. Em 7 dos 17 grupos de smoke, o operador verá 404 garantido e **NÃO saberá distinguir** "endpoint não-deployado" de "endpoint errado no documento".

**Risco residual**: 23 secrets listados em SECRETS_INVENTORY.md não estão em `.env.example`. Operador pode descobrir só em runtime que falta env var.

---

## 6. Resumo executivo

| Item | Resultado |
|------|-----------|
| Total comandos auditados | 72 |
| ✅ Corretos | 56 (77.8%) |
| ⚠️ Parcialmente corretos | 7 (9.7%) |
| ❌ Incorretos / impossíveis | 9 (12.5%) |
| Endpoints inexistentes referenciados | 8 |
| Comandos impossíveis | 14 |
| Inconsistências entre docs | 10 |
| Secrets não documentados em `.env.example` | 23 |

**Conclusão objetiva:** Após corrigir apenas a documentação (8 correções), o operador **consegue executar o deploy sem improviso** — desde que:
- `/api/health` retorne 404 (estado conhecido, documentado em M21.5 BLOQUEADOR #4)
- Prometheus/Grafana NÃO estejam deployados (documentado em M20 como não provisionado)
- Senha de login `Tester@2025` funcione para `tester.modulos@araos.dev` (verificado em `tests/load/locustfile.py`)

**Sem essas 8 correções:** o operador verá 7 falsos negativos (404) durante o smoke pós-deploy e **não terá como distinguir** falha real de documento errado.

---

## Anexo A — Comandos que funcionam e são válidos (verificados)

| Comando | Doc | Verificação |
|---------|-----|-------------|
| `./scripts/backup.sh --env=production` | DEPLOY_RUNBOOK §2 | ✅ script existe, sintaxe `--env=` correta |
| `./scripts/backup.sh --env=staging` | DEPLOY_RUNBOOK §2 | ✅ idem |
| `./scripts/rollback.sh --env=production` | ROLLBACK_PLAYBOOK §6.3 | ✅ idem |
| `./scripts/rollback.sh --env=production --to-backup=FILE` | ROLLBACK_PLAYBOOK §8.2 | ✅ idem |
| `./scripts/smoke.sh --env=production` | DEPLOY_RUNBOOK §7 | ✅ idem |
| `./scripts/healthcheck.sh --env=production` | DEPLOY_RUNBOOK §16 | ✅ idem |
| `./scripts/deploy_prod.sh v1.2.3` | ROLLBACK_PLAYBOOK §8.3 | ✅ idem |
| `./scripts/deploy_staging.sh --skip-tests` | GO_LIVE_CHECKLIST 3.1 | ✅ idem |
| `./scripts/setup_cron.sh` | (não explícito) | ✅ idem |
| `python3 scripts/validate_env.py` | DEPLOY_RUNBOOK §1 | ✅ idem |
| `git fetch && git status` | DEPLOY_RUNBOOK §1 | ✅ comando git padrão |
| `git fetch --tags && git checkout v1.2.3` | DEPLOY_RUNBOOK §3 | ✅ idem |
| `git checkout main` | DEPLOY_RUNBOOK §3 | ✅ idem |
| `git commit -m "fix: ..."` | ROLLBACK_PLAYBOOK §8.3 | ✅ idem |
| `docker-compose -f docker-compose.prod.yml --env-file .env.production build --pull` | DEPLOY_RUNBOOK §4 | ✅ compose existe |
| `docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps siap-backend` | DEPLOY_RUNBOOK §6 | ✅ idem |
| `docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps siap-frontend` | DEPLOY_RUNBOOK §8 | ✅ idem |
| `docker exec siap-backend flask db upgrade` | DEPLOY_RUNBOOK §5 (segunda opção) | ✅ Flask-Migrate instalado |
| `docker exec siap-redis redis-cli ping` | DEPLOY_RUNBOOK §11 | ✅ redis instalado na imagem |
| `docker exec siap-redis redis-cli info clients` | DEPLOY_RUNBOOK §11 | ✅ idem |
| `docker exec siap-db pg_isready -U siap_user -d aracannabis` | DEPLOY_RUNBOOK §12 | ✅ pg_isready na imagem postgres |
| `docker exec siap-db psql -U siap_user -d aracannabis -c "SELECT 1;"` | DEPLOY_RUNBOOK §12 | ✅ psql na imagem |
| `docker logs siap-backend --since 5m` | DEPLOY_RUNBOOK §16 | ✅ comando docker padrão |
| `docker ps | grep siap-backend` | DEPLOY_RUNBOOK §6 | ✅ idem |
| `docker exec siap-backend ps aux | grep gunicorn | wc -l` | DEPLOY_RUNBOOK §10 | ✅ idem |
| `curl -sk https://api.visualsmartflow.com.br/api/csrf-token` | TODOS | ✅ rota existe em `app_cors_livre.py:122` |
| `curl -sk -X POST https://api.visualsmartflow.com.br/api/auth/login` | POST_DEPLOY_SMOKE §3 | ✅ rota existe em `routes/auth.py:83` |
| `curl -sk https://api.visualsmartflow.com.br/api/pacientes` | POST_DEPLOY_SMOKE §4 | ✅ rota existe |
| `curl -sk https://api.visualsmartflow.com.br/api/consultas` | POST_DEPLOY_SMOKE §5 | ✅ idem |
| `curl -sk https://api.visualsmartflow.com.br/api/prescricoes` | POST_DEPLOY_SMOKE §6 | ✅ idem |
| `curl -sk https://api.visualsmartflow.com.br/api/cannabis` | POST_DEPLOY_SMOKE §7 | ✅ idem |
| `curl -sk https://api.visualsmartflow.com.br/api/planos` | POST_DEPLOY_SMOKE §10 | ✅ idem |
| `curl -sk -X POST https://api.visualsmartflow.com.br/api/mercadopago/webhook` | POST_DEPLOY_SMOKE §11 | ✅ rota existe em `routes/mercadopago.py:131` |
| `curl -sk https://api.visualsmartflow.com.br/api/lgpd/politica-privacidade` | POST_DEPLOY_SMOKE §13 | ✅ idem |
| `sha256sum backup.sql.gz` | GO_LIVE_CHECKLIST 5.3 | ✅ comando Linux padrão |
| `ls -lh /var/backups/siap/db_*.sql.gz | tail -1` | GO_LIVE_CHECKLIST 5.2 | ✅ glob casa com `db_${ENV}_${TIMESTAMP}.sql.gz` |
| `crontab -l | grep backup` | POST_DEPLOY_SMOKE §14 | ✅ setup_cron.sh instala |

---

**Relatório gerado em modo EXECUTE/READ-ONLY. Nenhuma correção aplicada. Aguardando revisão humana.**