# RELEASE_MANIFEST.md — AraOS SIAP v1.0.0-rc.1

**Data:** 2026-06-28
**Release Candidate:** `v1.0.0-rc.1`
**Origem:** M33 — RC1 Assembly
**Modo:** Manifest (somente leitura; não é release físico)

---

## 1. Commit do RC1

**Tag Git:** `v1.0.0-rc.1` (pendente de criação)
**Branch de release:** `fix/p0-stabilization-2026-06` (HEAD atual)
**Base anterior:** `2222183 feat(araflow): core integration harness (sprint 3.5)`

### Hash do commit RC1

```
REDACTED
```

### Quantidade de commits novos

**21 commits** desde a base `2222183` (todos com Conventional Commits).

### Lista completa (mais recente primeiro)

| # | Hash | Tipo | Escopo | Mensagem resumida |
|---|------|------|--------|-------------------|
| 1 | `7c0e6e1` | chore | docs | add araflow docs and remaining artifacts |
| 2 | `70e55d5` | chore | docs | add operational docs and adrs |
| 3 | `2bb94f5` | chore | docs | add repository organization docs for rc1 |
| 4 | `b88e193` | feat | monorepo | add araflow sprint 0 subprojects |
| 5 | `a18b690` | chore | configs | add monorepo tooling configs |
| 6 | `2694868` | feat | frontend | pages, contexts and services from m23 to m25 |
| 7 | `4bc853e` | feat | frontend | consolidate component updates from m23 to m25 |
| 8 | `355675d` | feat | frontend | add hooks directory and theme infrastructure |
| 9 | `d877664` | feat | frontend | add error pages (403, 404, 500, 401) |
| 10 | `fc236b4` | feat | frontend | add reusable ui components |
| 11 | `d55a4e9` | chore | gitignore,envs | harden gitignore and update envs examples |
| 12 | `a4e3c86` | chore | infra | backup, restore, rollback, smoke and cd workflows |
| 13 | `6273b63` | feat | deploy | deploy_guard, /api/schema-version and 12 tests (m28) |
| 14 | `9295e1c` | feat | security | require_secret and assert_required_secrets_on_startup |
| 15 | `aeb9da6` | feat | tenant | tenant middleware and webhook auth hardening |
| 16 | `adf83f9` | feat | routes | clinica management, modulos, hc report and ai |
| 17 | `05fe9ee` | fix | routes | p0 hardening in auth, mercadopago, webhooks and others |
| 18 | `e4ef818` | fix | evolucoes | data range and texto limite (bug-alt-04/08) |
| 19 | `67ca2b2` | fix | exames | accept json content-type in criar_exame (bug-alt-01) |
| 20 | `dec877b` | fix | pacientes | p0 validation and duplicate cpf (bug-alt-03..07) |
| 21 | `ce67388` | chore | migration | add data_revogacao column migration (b-001) |

### Estatísticas dos 21 commits

- **Arquivos modificados:** 321
- **Linhas adicionadas:** ~25.000
- **Linhas removidas:** ~13.000
- **Working tree:** ✅ **LIMPO** (verificado em `git status`)

---

## 2. Migrations

**Total:** 15 migrations (1 nova em M33)
**Root:** `0331305d2b3c` (Set/2025)
**Head:** `REDACTED` (Jun/2026, NOVO)
**Heads:** **1** (chain único, sem necessidade de merge)
**Órfãs:** **0**
**Duplicadas:** **0**
**Idempotentes:** **1** (B-001)

### Inventário completo

```
0331305d2b3c (root, Set/2025) — add_reminder_settings_table
    └─ ec450c16ec01 — REDACTED
        ├─ f3a8c9d2e1b4_add_catalog_fields ─┐
        └─ a1b2c3d4e5f6 — REDACTED
                                            └─ bb2cbd44835d (merge 1) ──┐
                                                                       ├─ 83c3e98787e1 — araos_week1_tenant_layer
                                                                       │   └─ ca1ef05ac0d2 — araos_week3_nervous_system
                                                                       │       └─ 9b93d2cb67d7 — araos_week4_clinical_intelligence
                                                                       │           └─ 791ba78aa8fb — araos_week5_agent_runtime
                                                                       │               │
                                                                       │               ├─ a7b8c9d0e1f2 (merge 2)
                                                                       │               │   └─ d3e4f5a6b7c8 — add_consultorios_table
                                                                       │               │       └─ 2026_06_17_clinica_management
                                                                       │               │           └─ 2026_06_21_add_modulos_tables
                                                                       │               │               └─ REDACTED (HEAD, B-001)
                                                                       │
                                                                       └─ 7b45916cd7fc — add_voice_session_tables
```

### Migration crítica para o release

| ID | Comando SQL |
|----|-------------|
| `REDACTED` | `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;` |

**Status atual em produção:** **NÃO aplicada** (B-001 ainda ativo, conforme M29).

---

## 3. Versão

| Componente | Versão |
|-----------|--------|
| AraOS SIAP | `1.0.0-rc.1` |
| API version (declarada em `app_cors_livre.py:136`) | `1.0.0` |
| Flask | 2.x (verificar em `requirements.txt`) |
| SQLAlchemy | 2.0 |
| Python | 3.11+ |
| Node (frontend) | _pendente verificação_ |

---

## 4. Docker

### Imagens

| Imagem | Tag | Base |
|--------|-----|------|
| `siap-backend` | `prod-<sha>` | `python:3.11-slim` |
| `siap-frontend` | `prod-<sha>` | `node:20-alpine` (build) + `nginx:alpine` (serve) |

### Dockerfile esperado

- `Dockerfile.backend` — entrypoint: `entrypoint_siap.sh`
- `Dockerfile.frontend` — multi-stage: build React + serve nginx

### Entrypoint (`entrypoint_siap.sh`)

Comportamento esperado (M22):
1. `flask db upgrade` (aplica migrations pendentes)
2. Inicia gunicorn

> **CRÍTICO:** Em produção, o pipeline NUNCA chama `flask db upgrade` (M30 descobriu). Operator deve rodar manualmente ou substituir entrypoint.

---

## 5. Compose

### Arquivos

| Arquivo | Ambiente |
|---------|---------|
| `docker-compose.yml` | dev local |
| `docker-compose.prod.yml` | produção |
| `docker-compose.staging.yml` | staging (criado em M22) |

### Serviços (produção)

| Serviço | Porta | Healthcheck |
|---------|-------|-------------|
| `backend` | 5002 | `/api/health` |
| `frontend` | 80 | nginx status |
| `postgres` | 5432 | pg_isready |
| `redis` | 6379 | PING |
| `nginx` (opcional) | 443 | — |

---

## 6. Secrets

### Obrigatórios (produção aborta startup se ausentes — P0-A FASE 4)

| Variável | Descrição |
|----------|-----------|
| `MERCADOPAGO_WEBHOOK_SECRET` | Assinatura HMAC do webhook MP |
| `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` | Webhook MP de módulos |
| `EVOLUTION_WEBHOOK_SECRET` | Webhook Evolution API |
| `DR_ANDERSON_WEBHOOK_SECRET` | Webhook Dr.Anderson |
| `INTERNAL_SERVICE_KEY` | Auth interna entre serviços |
| `JWT_SECRET_KEY` | Token JWT (>= 32 chars) |
| `SECRET_KEY` | Flask secret (>= 32 chars) |
| `CSRF_TOKEN` | Token CSRF (>= 32 chars) |
| `ANONYMIZATION_KEY` | Crypto para LGPD |
| `DATABASE_URL` | Conexão PostgreSQL |

### Validação

- Startup chama `assert_required_secrets_on_startup()` (M18 P0-A FASE 4)
- Em produção: aborta com `RuntimeError`
- Em dev/staging: loga warning

---

## 7. Testes incluídos

**Total:** 68 testes rastreados em `tests/`

### Suite organizada

| Tipo | Local | Quantidade |
|------|-------|-----------|
| Unit (raiz) | `tests/test_*.py` | 38 arquivos |
| Unit (deploy_guard) | `tests/test_deploy_guard.py` | 1 arquivo (12 testes) |
| Integration | `tests/integration/` | 1 arquivo |
| Security | `tests/security/` | 3 arquivos (P0 remediation + rate limit) |
| Smoke | `tests/smoke/` | 1 arquivo (webhook security) |
| E2E Playwright | `tests/e2e/test_*.py` | 13 arquivos (login → ia_chat) |
| Load (Locust) | `tests/load/locustfile.py` + `scenarios/` | 1 + 3 cenários |

### Smoke específico

| Tipo | Local | Total |
|------|-------|-------|
| Smoke webhook | `tests/smoke/test_webhook_security.py` | 1 arquivo |
| E2E Playwright | `tests/e2e/test_01_login.py` ... `test_13_ia_chat.py` | 13 arquivos |
| Carga Locust | `tests/load/locustfile.py` + `scenarios/` | 3 cenários |

### Comando

```bash
# Smoke contra produção
./scripts/smoke.sh --env=production

# Carga
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 50 -r 5 -t 5m
```

### Critérios de aceitação (M26)

| Critério | Valor |
|----------|-------|
| Taxa de erro | < 1% |
| Latência p95 | < 500ms |
| Latência p99 | < 2000ms |
| Throughput | >= 50 RPS |

---

## 8. Rollback

### Procedimento

```bash
./scripts/rollback.sh --env=production
```

### O que o script faz

1. Identifica a imagem anterior (`siap-backend:prod-<sha-anterior>`)
2. Para container atual (`docker compose down`)
3. Sobe container com imagem anterior
4. Roda smoke pós-rollback
5. Notifica Slack #deploys

### Backup pré-deploy

```bash
./scripts/backup.sh --env=production
# → /var/backups/siap/aracannabis_<timestamp>.sql.gz
# Retenção: 7 diários + 4 semanais + 12 mensais
```

---

## 9. Artefatos

### Documentação incluída

**Total:** 172 docs rastreados em `docs/` + 1 root (`RELEASE_MANIFEST.md`).

| Categoria | Quantidade | Caminho |
|-----------|-----------|---------|
| AraFlow (produto) | 39 | `docs/AraFlow/` |
| Audit Reports | 3 | `docs/AUDITORIA_*.md` |
| Release & Certificação | 11 | `docs/{GO_LIVE,RELEASE,PRODUCTION_*}.md` |
| Operacional (runbooks) | 12 | `docs/{DEPLOY,ROLLBACK,DISASTER_*}.md` |
| Segurança | 6 | `docs/{SECURITY,WEBHOOK_SECURITY,P0_*}.md` |
| LGPD / Compliance | 4 | `docs/{LGPD,AUDITORIA_LGPD,security_lgpd}.md` |
| Capacidade / Performance | 7 | `docs/{PERFORMANCE,LIGHTHOUSE,AUDITORIA_CAPACIDADE}.md` |
| Billing | 1 | `docs/BILLING_*.md` |
| Bugs / Issues | 10 | `docs/{BUG,DEAD,UI_INCONSISTENCIES,FRONTEND_*,FASE5_*}.md` |
| UX / Jornada | 5 | `docs/{USER_JOURNEY,UX_*,EVIDENCE_MATRIX,FUNCTIONAL_*}.md` |
| Validação | 7 | `docs/{BETA_READINESS,PLAYWRIGHT,STAGING_*,OPERATIONAL_*,RUNBOOK_*}.md` |
| Arquitetura / Especificação | 11 | `docs/{AI_CLINICAL,API_CONVENTIONS,ARAOS_*,ESPECIFICACAO_*}.md` |
| Sprints / Releases | 9 | `docs/WEEK*.md` |
| Sistemas implementados | 8 | `docs/SISTEMA_*.md` |
| ADRs (incluindo template) | 9 | `docs/adr/` |
| Histórico / Missoes | ~25 | `docs/{CAMPO,MELHORIAS,SOLUÇÃO,VERSÃO,INSTRUÇÕES,*}.md` |
| Indice e Manifests | 3 | `docs/INDEX.md`, `docs/RELEASE_*.md`, `docs/REPOSITORY_*.md` |

### Versionados (no repositório)

| Categoria | Localização |
|-----------|-------------|
| Backend | `app_cors_livre.py`, `config.py`, `routes/`, `services/`, `middleware/`, `models.py`, `models_extra.py`, `models_modulos.py`, `tenant_lib.py`, `security_config.py` |
| Frontend | `frontend/src/` (components, pages, services, contexts, hooks, theme) |
| Migrations | `migrations/versions/` (15 arquivos) |
| Testes | `tests/` (38 root + 4 subdirs organizados) |
| Infra | `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/`, `scripts/`, `entrypoint_siap.sh` |
| Documentação | `docs/` (172 arquivos + AraFlow/) |
| Monorepo AraFlow | `mobile/`, `monitoring/`, `shared-contracts/`, `tools/araflow-cli/`, `backend/` |
| Configs de tooling | `.editorconfig`, `.eslintrc.cjs`, `.prettierrc.json`, `.lintstagedrc.json`, `commitlint.config.cjs`, `.nvmrc`, `.npmrc`, `.husky/` |

### NÃO versionados (proposta M32)

| Artefato | Onde | Por quê |
|----------|------|---------|
| `reports/load_*.html` | 4.7 MB | Artefato de teste de carga (Locust) |
| `instance/*.db` | 492 KB | SQLite local |
| `htmlcov_week6/` | ~10 MB | Coverage HTML de uma sprint |
| `venv_local/` | ~100 MB | Virtualenv local |
| `AGENDA.png`, `eusoulia.png` | < 1 MB | Imagens avulsas sem contexto |
| `qrcode_eusoulia.png` | < 1 MB | QR avulso (já em .gitignore) |
| `tools/araflow-cli/node_modules/` | ~50 MB | Dependências npm |

**Total estimado:** ~165 MB que NÃO devem entrar no Git.

### Configurações de tooling (recomendadas para commit)

```
.editorconfig
.eslintrc.cjs
.prettierrc.json
.prettierignore
.lintstagedrc.json
commitlint.config.cjs
.nvmrc
.npmrc
.lighthouserc.json
tsconfig.base.json
tsconfig.json
package.json
package-lock.json
.husky/
```

---

## 10. Pendências para o release

### Bloqueadores

- [ ] Migration B-001 aplicada em produção (operador)
- [ ] 7 commits principais executados (dev)
- [ ] Tag `v1.0.0-rc.1` criada (dev)
- [ ] Imagem Docker buildada + push (CI/CD)
- [ ] Deploy executado (operador)
- [ ] Smoke pós-deploy verde (qualquer um)

### Recomendados (não-bloqueantes)

- [ ] Atualizar 11 docs antigos para `docs/archive/` (próximo ciclo)
- [ ] Reorganizar 38 testes em `tests/` raiz para subcategorias (próximo ciclo)
- [ ] Mover `AraFlow/` para fora do repo de SIAP (quando AraFlow virar release independente)
- [ ] Adicionar CI que valida `pytest tests/` antes de merge

---

## 11. Riscos conhecidos (carry-over)

| Risco | Origem | Status |
|-------|--------|--------|
| **B-001** — data_revogacao ausente em produção | M26/M27 | Pendente migration |
| Webhooks dr-anderson/tenant sem auth (200 sem assinatura) | M29 | P1 — beta fechado |
| Rate limit desativado em /auth/login | M29 | P1 — beta fechado |
| Tenant isolation com X-Association-ID retorna 403 sempre | M29 | P2 |
| Sem alerting automatizado em runtime | M29 | P2 |
| Working tree 269 entradas não commitadas | M31/M32 | Pendente commit |

---

**Fim do manifest.** Próxima ação: executar sequência de 9 commits conforme M31 FASE 3 (após migration B-001 aplicada).