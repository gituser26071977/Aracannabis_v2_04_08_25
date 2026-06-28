# RELEASE_PREPARATION_REPORT — MISSÃO 31

**Data:** 2026-06-27
**Modo:** EXECUTE (somente preparação, sem execução de commit/deploy)
**Origem:** M31 — Transformar estado atual em release reproduzível
**Tag proposta:** `v1.0.0-rc.1` (primeira Release Candidate oficial)

---

# Sumário executivo

**Working tree atual:** 268 entradas (94 modified + 174 untracked)
**Versão atual em produção:** código de 20/06/2026 (commit `a2e4131`), 7+ dias atrás
**Bloqueador principal:** migration `data_revogacao` (B-001) ainda não aplicada em produção
**Recomendação:** seguir o plano de 7 commits descrito abaixo + 8 passos da M30 para chegar a GO CONDICIONAL

---

## FASE 1 — Audit do working tree

### Estatísticas gerais

| Tipo | Quantidade |
|------|-----------|
| Modificados (M) | 94 |
| Untracked (??) | 174 |
| Added staged (A) | 0 |
| Deleted (D) | 0 |
| **TOTAL** | **268** |

### Classificação por categoria

#### BACKEND — Modificado (23 arquivos)

```
 M app_cors_livre.py              # P0-A FASE 4 — assert_required_secrets_on_startup
 M config.py                       # require_secret()
 M security_config.py              # CSP, sanitização, is_valid_cpf
 M tenant_lib.py                   # filtros tenant
 M middleware/tenant_middleware.py
 M middleware/webhook_auth.py
 M services/webhook_handler.py
 M routes/auth.py                  # melhorias auth
 M routes/pacientes.py             # M25: P0/P1 fixes (BUG-ALT-03/04/05/06/07)
 M routes/evolucoes.py             # M25: BUG-ALT-04/08 (range data, limite texto)
 M routes/exames.py                # M25: BUG-ALT-01 (aceita JSON)
 M routes/mercadopago.py           # webhook auth
 M routes/cadastro_profissionais.py
 M routes/dr_anderson_webhook.py
 M routes/dynamic_tenant_webhook.py
 M routes/webhooks.py
 M routes/ai_chat_simples.py
 M routes/anamneses.py
 M routes/anuncios.py
 M routes/crew_ai.py
 M routes/hc_report.py
 M routes/modulos.py
 M routes/voice.py
```

#### BACKEND — Untracked (11 arquivos)

```
?? services/deploy_guard.py                # M28: guard de migrations + schema
?? services/webhook_auth.py                # assert_required_secrets_on_startup
?? tests/test_deploy_guard.py              # M28: 12 testes
?? migrations/versions/REDACTED.py  # B-001 fix
?? scripts/_apply_p0_*.py                  # M18 scripts de P0 fix
?? backend/                                # ?? diretório com package.json
```

#### FRONTEND — Modificado (82 arquivos)

| Subpasta | Modificados |
|----------|-------------|
| frontend/src/components/ | 37 |
| frontend/src/pages/ | 25 |
| frontend/src/services/ | 4 |
| frontend/src/pages/association/ | 4 |
| frontend/src/contexts/ | 2 |
| frontend/src/components/catalogo/ | 2 |
| frontend/src/pages/patient/ | 2 |
| frontend/src/components/voice/ | 1 |
| frontend/src/hooks/ | 1 |
| frontend/src/theme/ | 1 |
| frontend/src/App.js | 1 |
| frontend/src/components/{AdBanner,BeckDepressionTest,CalendarioConsultas,...}.js | (37 componentes) |

#### INFRA / DOCKER / CI — Untracked (12+ arquivos)

```
?? .github/                                # workflows CI/CD
?? docker-compose.staging.yml              # staging environment
?? scripts/backup.sh                       # 7+4+12 retention
?? scripts/restore.sh
?? scripts/rollback.sh
?? scripts/deploy_prod.sh
?? scripts/deploy_staging.sh
?? scripts/healthcheck.sh
?? scripts/smoke.sh
?? scripts/setup_cron.sh
?? scripts/p0a_audit_alembic.sh
?? scripts/p0a_fix_data_revogacao.sh       # B-001 emergency fix
?? scripts/p0a_validate_data_revogacao_fix.sh
```

#### DOCS — Untracked (107+ arquivos)

```
?? README.md
?? CONTRIBUTING.md
?? docs/AUDITORIA_*.md (3)
?? docs/AraFlow/* (39+ documentos)
?? docs/BETA_*.md
?? docs/BUG_*.md
?? docs/DEPLOY_*.md
?? docs/DISASTER_*.md
?? docs/RELEASE_*.md
?? docs/GO_LIVE_*.md
?? docs/M2*.md (relatórios de missões)
?? PLANO_CORRECOES_AUDITORIA_2026_06.md
?? RELATORIO_TESTE_CARGA_2026_06.md
```

#### TESTES — Untracked

```
?? tests/test_deploy_guard.py              # M28: 12 testes
?? tests/e2e/                              # Playwright tests
?? tests/load/                             # Locust scenarios
?? tests/security/                         # P0/security tests
?? tests/smoke/                            # smoke tests
```

#### TOOLS / MOBILE / MONITORING — Untracked

```
?? tools/araflow-cli/                      # ~50 arquivos — CLI TS
?? mobile/                                 # Expo/React Native — app.json, src/, etc.
?? monitoring/                             # Prometheus, alertmanager
?? shared-contracts/                       # contratos AraFlow
?? backend/                                # TS backend (??)
```

#### CONFIGS — Untracked

```
?? .editorconfig
?? .eslintrc.cjs
?? .prettierrc.json / .prettierignore
?? .npmrc / .nvmrc
?? .lighthouserc.json
?? .lintstagedrc.json
?? commitlint.config.cjs
?? .husky/
?? tsconfig.base.json / tsconfig.json
?? package.json / package-lock.json        # root package
?? .env.staging / .env.staging.example     # staging env
```

---

## FASE 2 — Blocos lógicos (separação por Release)

### Release A — `v1.0.0-rc.1` (RC para beta fechado)

**O que entra:**
- ✅ Migration `data_revogacao` (resolve B-001)
- ✅ M25 P0/P1 fixes (BUG-ALT-01..08) — validações de paciente, exames, evoluções
- ✅ M28 deploy_guard + schema-version endpoint + 12 testes
- ✅ Pipeline CD (cd-production.yml + cd-staging.yml)
- ✅ Scripts de backup/restore/rollback/smoke/healthcheck
- ✅ Documentação operacional (DEPLOY_RUNBOOK, ROLLBACK_PLAYBOOK, DISASTER_RECOVERY_REPORT)

**Por que neste release:** corrige o blocker B-001 e adiciona o guard que blinda contra recorrência. Essencial para abrir beta.

### Release B — `v1.0.0` (release estável após beta)

**O que entra:**
- ⏳ Demais modificações do working tree (rotas, services, frontend polishing)
- ⏳ AraFlow docs (39+ arquivos)
- ⏳ Mobile/Expo
- ⏳ tools/araflow-cli
- ⏳ monitoring/Prometheus

**Por que adiado:** não-bloqueante para beta. Estabiliza após feedback real de 5 médicos.

### Release C — `v1.1.0` (próxima minor)

**O que entra:**
- ⏸️ Refactor de UI/UX
- ⏸️ AI Compliance (v1.5.0-ai-compliance)
- ⏸️ Novas funcionalidades (Sprint 3 AraFlow, etc.)

---

## FASE 3 — Sequência ideal de commits

> ⚠️ **Sequência proposta, NÃO executada.** Esta é a ordem ideal para minimizar risco e permitir rollback granular.

### Commit 1: `chore(migration): add data_revogacao column migration (B-001)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `migrations/versions/REDACTED.py` |
| **Mensagem** | `chore(migration): add data_revogacao column migration (B-001)` |
| **Risco** | Baixo — migration idempotente (`ADD COLUMN IF NOT EXISTS`) |
| **Rollback** | `ALTER TABLE pacientes DROP COLUMN data_revogacao;` |

### Commit 2: `fix(pacientes): P0 validation + duplicate CPF check (BUG-ALT-03/04/05/06/07)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `routes/pacientes.py`, `security_config.py` |
| **Mensagem** | `fix(pacientes): P0 validation + duplicate CPF check (BUG-ALT-03/04/05/06/07)` |
| **Risco** | Médio — pode rejeitar entradas edge-case que antes passavam |
| **Rollback** | `git revert <hash>` |

### Commit 3: `fix(exames): accept JSON content-type in criar_exame (BUG-ALT-01)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `routes/exames.py` |
| **Mensagem** | `fix(exames): accept JSON content-type in criar_exame (BUG-ALT-01)` |
| **Risco** | Baixo — adiciona novo caminho, mantém o antigo |
| **Rollback** | `git revert <hash>` |

### Commit 4: `fix(evolucoes): data range + texto limite (BUG-ALT-04/08)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `routes/evolucoes.py` |
| **Mensagem** | `fix(evolucoes): data range (2000-01-01..today) + texto limite 10k chars (BUG-ALT-04/08)` |
| **Risco** | Baixo |
| **Rollback** | `git revert <hash>` |

### Commit 5: `feat(security): require_secret() + assert_required_secrets_on_startup (P0-A FASE 4)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `config.py`, `services/webhook_auth.py`, `app_cors_livre.py`, `security_config.py` |
| **Mensagem** | `feat(security): require_secret() + assert_required_secrets_on_startup (P0-A FASE 4)` |
| **Risco** | Alto — aborta startup se secrets faltarem |
| **Rollback** | `git revert <hash>` + setar env vars faltantes |

### Commit 6: `feat(deploy): deploy_guard + /api/schema-version endpoint + 12 tests (M28)`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `services/deploy_guard.py`, `tests/test_deploy_guard.py`, `app_cors_livre.py` (rota) |
| **Mensagem** | `feat(deploy): deploy_guard + /api/schema-version endpoint + 12 tests (M28)` |
| **Risco** | Alto — aborta startup em produção se migration divergente |
| **Rollback** | `ENABLE_DEPLOY_GUARD=0` antes de subir container |

### Commit 7: `chore(infra): backup/restore/rollback/smoke/healthcheck scripts + CD workflows`

| Item | Conteúdo |
|------|----------|
| **Arquivos** | `scripts/{backup,restore,rollback,smoke,healthcheck,deploy_prod,deploy_staging,setup_cron}.sh`, `.github/workflows/*.yml`, `docker-compose.staging.yml`, `entrypoint_siap.sh` |
| **Mensagem** | `chore(infra): backup/restore/rollback/smoke/healthcheck scripts + CD workflows` |
| **Risco** | Baixo — não altera código de aplicação |
| **Rollback** | `git revert <hash>` |

### Commits opcionais (adiáveis)

- Commit 8: `chore(docs): adicionar relatórios de missões M17-M30` — risco baixo, valor de auditoria
- Commit 9: `fix(frontend): ajustes polimento` — risco médio, pode quebrar UI
- Commit 10: `feat(mobile): Expo app skeleton` — risco alto, módulo novo

### Resumo da sequência

| # | Tipo | Risco | Reversível |
|---|------|-------|-----------|
| 1 | chore(migration) | Baixo | ✅ fácil |
| 2 | fix(pacientes) | Médio | ✅ fácil |
| 3 | fix(exames) | Baixo | ✅ fácil |
| 4 | fix(evolucoes) | Baixo | ✅ fácil |
| 5 | feat(security) | Alto | ⚠️ médio (env vars) |
| 6 | feat(deploy) | Alto | ⚠️ médio (env var) |
| 7 | chore(infra) | Baixo | ✅ fácil |

---

## FASE 4 — Arquivos que nunca deveriam entrar no Git

### Já ignorados pelo `.gitignore` atual (verificado)

```
*.db, *.sqlite3, *.log, logs/, uploads/, venv/, build/, dist/, node_modules/
.env, .env.local, .env.development.local, .env.production.local
*.pem, *.p12, *.pfx, *.key
coverage/, htmlcov/, htmlcov_week6/
__pycache__/, *.pyc
```

### NÃO ignorados mas deveriam estar (FALTA adicionar ao .gitignore)

| Arquivo/Pasta | Razão |
|---------------|-------|
| `reports/` | Artefatos de teste de carga (HTML+CSV, 4.6 MB) |
| `instance/aracannabis.db` | SQLite local (banco de desenvolvimento) |
| `Backup/aracannabis.tar.gz` | Backup local antigo |
| `htmlcov_week6/` | Coverage HTML de uma sprint específica |
| `frontend/frontend_dev.log` | Log de dev |
| `venv_local/` | Virtualenv local |
| `AGENDA.png`, `eusoulia.png` | Imagens avulsas (sem contexto) |
| `coverage/`, `htmlcov/`, `htmlcov_week6/` | Já parcialmente ignorado, mas htmlcov_week6 não está |
| `tools/araflow-cli/node_modules/` | (provavelmente ignorado) |

### `.gitignore` precisaria ser atualizado para incluir:

```gitignore
# Reports
reports/
*.html

# Local artifacts
instance/
Backup/
htmlcov*/
*.db-wal
*.db-shm

# Dev artifacts
frontend_dev.log
AGENDA.png
eusoulia.png
```

### Classificação de risco de commit

| Status | Contagem |
|--------|----------|
| Deveria ser commitado | ~80% dos 268 |
| NÃO deveria ser commitado | ~15% (relatórios, logs, sqlite, coverage) |
| Decisão ambígua | ~5% (mobile/, tools/araflow-cli/, monitoring/) |

---

## FASE 5 — Migration audit

### Inventário (15 migrations)

| # | Revision | Nome | Idempotente? |
|---|----------|------|--------------|
| 1 | `0331305d2b3c` | add_reminder_settings_table | ❌ |
| 2 | `ec450c16ec01` | REDACTED | ❌ |
| 3 | `f3a8c9d2e1b4` | add_catalog_fields | ❌ |
| 4 | `bb2cbd44835d` | merge_heads | n/a (merge) |
| 5 | `83c3e98787e1` | araos_week1_tenant_layer | ❌ |
| 6 | `7b45916cd7fc` | add_voice_session_tables | ❌ |
| 7 | `ca1ef05ac0d2` | araos_week3_nervous_system | ❌ |
| 8 | `9b93d2cb67d7` | araos_week4_clinical_intelligence | ❌ |
| 9 | `791ba78aa8fb` | araos_week5_agent_runtime | ❌ |
| 10 | `a7b8c9d0e1f2` | add_conselho_tipo_to_profissionais | ❌ |
| 11 | `d3e4f5a6b7c8` | add_consultorios_table | ❌ |
| 12 | `2026_06_17_clinica_management` | clinica_management_flag | ❌ |
| 13 | `2026_06_21_add_modulos` | add_modulos_tables | ❌ |
| 14 | `REDACTED` | **(B-001 fix)** | ✅ **SIM** |
| 15 | `a1b2c3d4e5f6` | REDACTED | ❌ |

### Chains (grafos de dependência)

```
                    0331305d2b3c (raiz)
                          ↓
                    ec450c16ec01
                       ↙     ↘
        f3a8c9d2e1b4    a1b2c3d4e5f6 (chain 4)
            ↓
        bb2cbd44835d (merge)
        ↙              ↘
83c3e98787e1         7b45916cd7fc
    ↓                   ↓
ca1ef05ac0d2       a7b8c9d0e1f2
    ↓                   ↓
9b93d2cb67d7       d3e4f5a6b7c8
    ↓                   ↓
791ba78aa8fb    2026_06_17_clinica_management
(HEAD 1)              ↓
                2026_06_21_add_modulos
                       ↓
              REDACTED (HEAD 2)
```

### Heads (terminais, sem sucessores)

- `791ba78aa8fb` (chain Week 5)
- `REDACTED` (chain 2026)
- `a1b2c3d4e5f6` (chain Billing v2)

### Migrations órfãs

**Nenhuma.** Todas as 14 migrations não-raiz têm `down_revision` apontando para uma revision existente.

### Análise de risco

| Risco | Descrição | Mitigação |
|-------|-----------|-----------|
| **4 chains paralelas** | Não há merge único. Multi-head alembic pode causar confusão | Criar merge migration único |
| **14/15 migrations não idempotentes** | Aplicar `flask db upgrade` em DB com `db.create_all()` falha | Para produção, só aplicar a B-001 (idempotente) |
| **Migration raiz sem cabeça única** | `0331305d2b3c` é a raiz mas não tem "single linear chain" | Migrations antigas OK; nova chain 2026_06_22 é o futuro |
| **Migration B-001 OK** | Idempotente, sem lock, NULL column | Pode ser aplicada direto via SQL |

### Recomendação para o Release 1.0

1. **Criar merge migration** unificando as 4 heads — decisão de refactor de migrations (NÃO executar em M31)
2. **Adotar convenção:** toda migration nova DEVE ser idempotente (`ADD COLUMN IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`)
3. **Não rodar** `flask db upgrade` em produção sem antes auditar idempotência — usar SQL direto para B-001

---

## FASE 6 — CHANGELOG.md do Release 1.0

> Documento a ser gerado. Conteúdo proposto:

```markdown
# Changelog — AraOS v1.0.0-rc.1

**Data:** 2026-06-27
**Tag:** v1.0.0-rc.1
**Origem:** M31 — Release Preparation

---

## Security

- **M18:** P0-A FASE 4 — abortar startup em produção se secrets de webhook faltarem
- **M18:** require_secret() em config.py para validar presença de segredos
- **M18:** CSRF protection com tokens >= 32 chars
- **M18:** Rate limiting em /auth/login (configurável por decorator)
- **M18:** Validação de assinatura HMAC para webhooks (mercadopago, evolution, dr-anderson)
- **M20:** CSP, HSTS, X-Frame-Options, X-Content-Type-Options headers
- **M20:** /api/health endpoint (verifica DB, Redis, secrets)

## LGPD

- **M27:** Migration `data_revogacao` (B-001) — coluna obrigatória para art. 18, IX
- **M28:** Deploy guard valida presença de colunas críticas em information_schema

## Billing

- **M19:** Planos canônicos (Básico, Premium, Enterprise) seed automático
- **M19:** Gating por plano em rotas de clínica
- **M25:** Validação de CPF em cadastro (BUG-ALT-05) — prepara para cobrança

## Frontend

- **M22-M25:** Refatorações de UI (renomeação "Associação" → "Gestão da Clínica")
- **M23:** Páginas de Planos, Nutrologia, Agentes SDR migradas antd → MUI
- **M25:** Componentes de modulos adicionados (ModulosPage, ModuleGate)

## UX

- (Sem mudanças de UX nesta release)

## Infra

- **M18:** pipeline CD 9-estágios (build, lint, test, security, smoke, playwright, lighthouse, backup, deploy)
- **M22:** scripts de backup/restore/rollback/healthcheck
- **M22:** entrypoint_siap.sh com `flask db upgrade`
- **M23:** Docker Compose staging environment
- **M28:** deploy_guard.py — assertions de migrations + schema
- **M28:** endpoint `/api/schema-version` para observabilidade de schema

## Performance

- **M23:** Load test validou p95 < 500ms em carga leve (5 users)

## Deploy

- **M28:** Pipeline agora aborta startup em produção se migrations divergentes
- **M30:** Diagnóstico: produção estava 7+ dias atrás do repo — corrigir antes do release

## Breaking Changes

- **BUG-ALT-04:** data_nascimento < 1900 ou > hoje agora rejeitada (era aceita)
- **BUG-ALT-05:** CPF inválido (DV incorreto, alfabético) agora rejeitado (era aceito)
- **BUG-ALT-06:** nome vazio/só espaços/< 2 chars agora rejeitado
- **BUG-ALT-07:** nome > 200 chars agora rejeitado
- **BUG-ALT-08:** nota_evolucao > 10000 chars agora rejeitada

## Known Issues

- **B-001:** data_revogacao ausente em produção até que migration seja aplicada
- **M29:** Webhooks dr-anderson e tenant retornam 200 sem assinatura (P1)
- **M29:** Rate limit /auth/login parece desativado em produção (P1)
- **M29:** Tenant isolation com X-Association-ID sempre 403 (provavelmente P2)
- **M30:** 130+ arquivos modificados não commitados; working tree diverge de HEAD
```

---

## FASE 7 — RELEASE_CHECKLIST.md

> Documento a ser gerado. Conteúdo proposto:

```markdown
# RELEASE_CHECKLIST.md — AraOS v1.0.0-rc.1

## 1. Pré-release (T-7)

- [ ] Working tree commitado em commits lógicos (7 commits da FASE 3)
- [ ] Tag `v1.0.0-rc.1` criada
- [ ] `.gitignore` atualizado (reports/, instance/, Backup/, htmlcov*/, *.png avulsos)
- [ ] CHANGELOG.md revisado
- [ ] RELEASE_PREPARATION_REPORT.md revisado
- [ ] Working tree limpo (`git status` = nada)

## 2. Backup (T-1)

- [ ] `./scripts/backup.sh --env=production`
- [ ] Verificar arquivo .sql.gz em `/var/backups/siap/`
- [ ] Tamanho > 0 (não-vazio)
- [ ] Timestamp atual

## 3. Migration (T-0)

- [ ] Operador com SSH ao banco de produção
- [ ] Aplicar SQL idempotente:
  ```bash
  psql ... -c "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;"
  ```
- [ ] Validar: `SELECT data_revogacao FROM pacientes LIMIT 1;`
- [ ] (Opcional) `psql ... -c "CREATE TABLE IF NOT EXISTS alembic_version (...); INSERT ..."`
- [ ] Verificar coluna aparece em `\d pacientes`

## 4. Deploy (T+0)

- [ ] GitHub Actions `cd-production.yml` rodou (build, lint, test, security, smoke)
- [ ] Imagem Docker `siap-backend:prod-<sha>` publicada
- [ ] `./scripts/deploy_prod.sh v1.0.0-rc.1` executado
- [ ] Container subiu sem `RuntimeError` (deploy_guard não abortou)
- [ ] `/api/schema-version` retorna 200 com `all_critical_columns_present=true`

## 5. Smoke (T+5min)

- [ ] `./scripts/smoke.sh --env=production`
- [ ] Login: 200
- [ ] GET /pacientes/: 200 (não 500)
- [ ] POST /pacientes/: 201
- [ ] GET /dashboard/stats: 200
- [ ] GET /evolucoes/paciente/1: 200
- [ ] GET /planos/meu-plano: 200

## 6. Rollback (se falhar em qualquer smoke)

- [ ] `./scripts/rollback.sh --env=production`
- [ ] Verificar container voltou para versão anterior
- [ ] Smoke novamente
- [ ] Notificar #deploys Slack
- [ ] Investigar root cause

## 7. Monitoramento (T+30min, T+1h, T+24h)

- [ ] /api/health retorna 200
- [ ] Logs em `/var/log/siap/` sem erros 500
- [ ] CPU < 50% em containers backend
- [ ] Memória < 80% em containers backend
- [ ] Conexões PG < 50% do pool_size
- [ ] Nenhum alerta em Sentry/Datadog

## 8. Comunicação

- [ ] Slack #deploys: release v1.0.0-rc.1 deployed
- [ ] GitHub Release criado com notas
- [ ] Email para médicos beta: "Sistema pronto para uso"

## 9. Pós-release (T+24h)

- [ ] Validar logs sem 500 inesperados
- [ ] Validar backups automáticos rodando
- [ ] Coletar feedback dos 5 médicos beta
- [ ] Decidir se promove v1.0.0-rc.1 → v1.0.0
```

---

## FASE 8 — Respondendo as 6 perguntas obrigatórias

### 1. Quantos commits ideais existem?

**7 commits principais** (propostos na FASE 3), mais 3 opcionais adíveis:

| # | Commit | Categoria |
|---|--------|-----------|
| 1 | `chore(migration): add data_revogacao` | migration |
| 2 | `fix(pacientes): P0 validation + duplicate CPF` | bug fix |
| 3 | `fix(exames): accept JSON` | bug fix |
| 4 | `fix(evolucoes): data range + texto limite` | bug fix |
| 5 | `feat(security): require_secret() + startup assert` | feature |
| 6 | `feat(deploy): deploy_guard + schema-version` | feature |
| 7 | `chore(infra): backup/restore/rollback/CD workflows` | infra |
| 8 (opcional) | `chore(docs): relatórios missões M17-M30` | docs |
| 9 (opcional) | `fix(frontend): polimento` | frontend |
| 10 (opcional) | `feat(mobile): Expo skeleton` | feature |

**Mínimo necessário para o release:** 7 commits.
**Recomendado para qualidade:** 7 + commit 8 (docs) = 8 commits.

### 2. Existe mudança perigosa misturada?

**SIM — 2 mudanças perigosas:**

| Mudança | Risco | Por que perigosa |
|---------|-------|------------------|
| **Commit 5 (`feat(security): require_secret`)** | Alto | Aborta startup em produção se secret faltar. Se `.env` de prod não tiver a var, container morre. |
| **Commit 6 (`feat(deploy): deploy_guard`)** | Alto | Aborta startup em produção se migration divergente. Pega B-001 mas também pode pegar outros. |

**Mitigação:** aplicar Commit 5 e 6 **APÓS** migration B-001 já ter sido aplicada em produção (PASSO 4 do plano M30). Caso contrário, o guard abortaria o deploy.

### 3. O working tree está pronto para commit?

**NÃO integralmente.**

| Problema | Severidade |
|----------|-----------|
| 268 entradas no working tree — muitas | precisa particionar em 7+ commits |
| `.gitignore` precisa atualização (reports/, instance/, htmlcov*/) | pré-condição |
| Working tree mistura features + bug fixes + docs | precisa separar |
| Nenhum commit atual referencia BUG-IDs | precisa ser adicionado nas mensagens |
| Frontend (82 arquivos) tem mudanças cosméticas | risco médio de regressão visual |

**Recomendação:** revisar e particionar ANTES do primeiro commit.

### 4. Qual seria a primeira tag oficial?

**`v1.0.0-rc.1`** (primeira Release Candidate oficial do AraOS)

Justificativa:
- Versão `1.0.0` sinaliza "primeira release oficial"
- Sufixo `-rc.1` sinaliza "Release Candidate, primeiro" — comunica que pode ter ajustes
- Convenção semver padrão (`v{major}.{minor}.{patch}-{prerelease}`)
- Compatível com GitHub Releases + auto-generate notes

**Evolução proposta:**
- `v1.0.0-rc.1` → primeira RC para beta fechado de 5 médicos
- `v1.0.0-rc.2` → correções durante beta
- `v1.0.0` → release estável após feedback positivo

### 5. Existe algum arquivo que nunca deveria ser commitado?

**SIM — múltiplos:**

| Arquivo/Pasta | Por quê | Tamanho |
|---------------|---------|---------|
| `reports/load_*.html` | Artefatos de teste de carga Locust | 4.6 MB |
| `reports/load_*.csv` | CSV de métricas de carga | 100+ KB |
| `instance/aracannabis.db` | SQLite de dev local | variável |
| `Backup/aracannabis.tar.gz` | Backup antigo local | variável |
| `htmlcov_week6/` | Coverage HTML | várias MB |
| `frontend/frontend_dev.log` | Log de desenvolvimento | variável |
| `venv_local/` | Virtualenv local | várias MB |
| `AGENDA.png`, `eusoulia.png` | Imagens avulsas sem contexto | < 1 MB |
| `tools/araflow-cli/node_modules/` | Dependências npm | várias MB |
| `migrations/__pycache__/` | Python cache | < 1 MB |
| `__pycache__/` (vários) | Python cache | < 1 MB |

**Total estimado de lixo:** ~50-100 MB

**Ação:** atualizar `.gitignore` ANTES de qualquer commit. Padrão recomendado:

```gitignore
# Relatórios Locust
reports/

# SQLite local
instance/
*.db
*.db-wal
*.db-shm

# Backups antigos
Backup/

# Coverage
coverage/
htmlcov*/
.coverage

# Logs
*.log
frontend_dev.log

# Virtualenvs
venv*/
.venv/

# Imagens avulsas sem contexto
AGENDA.png
eusoulia.png

# Tooling
tools/*/node_modules/
tools/*/dist/
tools/*/build/
```

### 6. Quanto tempo estima do primeiro commit até produção?

**~80 minutos** (1 hora e 20 minutos), conforme plano de 8 passos da M30:

| Etapa | Tempo | Responsável |
|-------|-------|-------------|
| 1. Atualizar `.gitignore` | 5 min | dev local |
| 2. Fazer 7 commits (sequência FASE 3) | 30 min | dev local + revisão |
| 3. Push + criar tag `v1.0.0-rc.1` | 5 min | dev local |
| 4. Backup pré-deploy | 15 min | operador SSH |
| 5. Aplicar migration B-001 em prod | 5 min | operador psql |
| 6. Deploy (cd-production.yml) | 20 min | GitHub Actions + operador |
| 7. Re-rodar M29 smoke + carga | 10 min | dev/QA |
| 8. Decisão GO CONDICIONAL | 5 min | dono do produto |
| **TOTAL** | **~80 min** | Distribuído |

**Não inclui:**
- Janela de manutenção agendada com stakeholders
- Tempo de revisão de PR (se houver)
- Atrasos por problemas imprevistos

---

## Restrições respeitadas

- ✅ Não corrigi bugs funcionais
- ✅ Não alterei UX
- ✅ Não alterei frontend
- ✅ Não criei features
- ✅ Sem commit executado
- ✅ Sem push
- ✅ Sem PR
- ✅ Sem alteração de código
- ✅ Tudo baseado em inspeção read-only do working tree

---

# DECISÃO FINAL

# **Working tree NÃO está pronto para commit direto.**

**Recomendação operacional:**

1. **Atualizar `.gitignore`** com padrões da FASE 4 (5 min)
2. **Particionar working tree em 7 commits** da FASE 3 (30 min de revisão)
3. **Aplicar migration B-001 em produção** ANTES dos commits 5 e 6 (Commit 5/6 com guard podem abortar startup)
4. **Criar tag `v1.0.0-rc.1`** após os 7 commits
5. **Executar plano de 8 passos da M30** (~80 min até GO CONDICIONAL)
6. **Beta fechado de 5 médicos por 2-4 semanas** antes de promover para `v1.0.0`

**Risco residual:** Commits 5 e 6 (security + deploy guard) têm risco ALTO. Aplicar com `ENABLE_DEPLOY_GUARD=0` na primeira subida, validar, depois ativar guard.

**Parando conforme instrução.** M31 concluída.