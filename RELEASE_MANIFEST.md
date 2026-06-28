# RELEASE_MANIFEST.md — AraOS SIAP v1.0.0-rc.1

**Data:** 2026-06-27
**Release Candidate:** `v1.0.0-rc.1`
**Origem:** M32 — Repository Stabilization
**Modo:** Manifest (somente leitura; não é release físico)

---

## 1. Commit esperado

**Tag Git:** `v1.0.0-rc.1`
**Branch de release:** `main`
**Working tree:** 269 entradas (94 modified + 175 untracked) — **NÃO commitadas**

### Commits pendentes (sequência proposta em M31)

| # | Hash esperado | Mensagem | Risco |
|---|---------------|----------|-------|
| 1 | _pendente_ | `chore(migration): add data_revogacao column migration (B-001)` | Baixo |
| 2 | _pendente_ | `fix(pacientes): P0 validation + duplicate CPF check (BUG-ALT-03/04/05/06/07)` | Médio |
| 3 | _pendente_ | `fix(exames): accept JSON content-type in criar_exame (BUG-ALT-01)` | Baixo |
| 4 | _pendente_ | `fix(evolucoes): data range + texto limite (BUG-ALT-04/08)` | Baixo |
| 5 | _pendente_ | `feat(security): require_secret() + assert_required_secrets_on_startup` | **Alto** |
| 6 | _pendente_ | `feat(deploy): deploy_guard + /api/schema-version endpoint + 12 tests` | **Alto** |
| 7 | _pendente_ | `chore(infra): backup/restore/rollback/smoke/healthcheck scripts + CD workflows` | Baixo |
| 8 | _pendente_ | `chore(gitignore): add patterns for reports/, instance/, htmlcov*/, avulsas` | Baixo |
| 9 | _pendente_ | `chore(docs): add docs/INDEX.md and RELEASE_MANIFEST.md` | Baixo |

> Commits 5 e 6 (security + deploy_guard) **exigem** migration B-001 já aplicada em produção antes do deploy.

---

## 2. Migrations

**Total:** 15 migrations
**Root:** `0331305d2b3c` (Set/2025)
**Head:** `REDACTED` (Jun/2026)
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

## 7. Smoke

### Suite

| Tipo | Local | Total |
|------|-------|-------|
| Smoke completo | `tests/smoke/test_webhook_security.py` | 1 arquivo |
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

### Versionados (no repositório)

| Categoria | Localização |
|-----------|-------------|
| Backend | `app_cors_livre.py`, `config.py`, `routes/`, `services/`, `middleware/`, `models.py`, `models_extra.py`, `models_modulos.py`, `tenant_lib.py`, `security_config.py` |
| Frontend | `frontend/src/` (components, pages, services, contexts, hooks, theme) |
| Migrations | `migrations/versions/` (15 arquivos) |
| Testes | `tests/` (38 root + 4 subdirs) |
| Infra | `Dockerfile*`, `docker-compose*.yml`, `.github/workflows/`, `scripts/`, `entrypoint_siap.sh` |
| Documentação | `docs/` (119 arquivos + AraFlow/) |
| Configs de tooling | `.editorconfig`, `.eslintrc.cjs`, `.prettierrc.json`, `.lintstagedrc.json`, `commitlint.config.cjs`, `.nvmrc`, `.npmrc` |

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