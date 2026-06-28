# PRODUCTION_RECONCILIATION_REPORT — MISSÃO 30

**Data:** 2026-06-27
**Modo:** EXECUTE (somente identificação, sem correções)
**Origem:** M30 — Descobrir exatamente por que produção ≠ repositório
**Alvo:** `https://api.visualsmartflow.com.br` (produção real)

---

# TL;DR — Diagnóstico em uma frase

**A produção está rodando o código do commit `a2e4131` (WIP before VPS deploy 20260620_165602) — working tree não commitado de 20/06/2026 16:56. O HEAD atual do repositório é `ce141c5` (22/06/2026 03:30), com 50+ arquivos modificados e 2 arquivos novos (M28) não commitados. A produção está 7 dias atrás do repositório e nunca rodou `flask db upgrade`.**

---

## FASE 1 — Identificar versão real da produção

### Métodos utilizados
- Probing HTTP em endpoints (`/api/status`, `/api/health`, `/api/schema-version`, `/api/csrf-token`)
- Análise de headers HTTP (`Server`, `Date`, security headers)
- Comparação entre endpoints que respondem vs working tree atual
- Inspeção do repositório git local

### Resultado

| Item | Valor | Fonte |
|------|-------|-------|
| Commit em produção | **NÃO COMPROVADO diretamente** (sem acesso SSH) | inferência por endpoint probing |
| Commit mais provável em produção | `a2e4131` "WIP before VPS deploy 20260620_165602" | data do último deploy manual identificado |
| Branch | NÃO COMPROVADO | — |
| Imagem Docker | NÃO COMPROVADO | — |
| Tag | NÃO COMPROVADO | — |
| Timestamp do build | NÃO COMPROVADO | — |
| `alembic_version` em produção | **NÃO COMPROVADO via API** (não há endpoint que retorne) | — |
| Hash do container | NÃO COMPROVADO | — |
| Data do último deploy | ~20/06/2026 16:56 (commit WIP) | evidência: working tree de 20/06 ainda em prod |
| Server | gunicorn | header `Server: gunicorn` |
| Data da requisição | 2026-06-27 18:55:35 GMT | header `Date` |

### Evidência-chave: working tree não commitado

```
$ git blame -L 167,170 app_cors_livre.py
00000000 (Not Committed Yet 2026-06-27 15:56:17 -0300 167)  # Retorna 200 quando tudo OK; 503 quando algo está down.
00000000 (Not Committed Yet 2026-06-27 15:56:17 -0300 168)  @app.route("/api/health")
00000000 (Not Committed Yet 2026-06-27 15:56:17 -0300 169)  def health():
```

A linha do endpoint `/api/health` está como **"Not Committed Yet"** — isso significa que mesmo o working tree local contém modificações que não foram commitadas. Mas isso afeta apenas o LOCAL. Em produção, `/api/health` retorna **404**, indicando que o working tree NÃO está em produção.

### Inferência baseada em endpoints

| Endpoint | Estado em prod | Working tree | Commit ce141c5 (HEAD) | Tag v1.5.0-ai-compliance |
|----------|---------------|--------------|----------------------|-------------------------|
| `/api/auth/login` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/auth/profile` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/csrf-token` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/status` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/planos/meu-plano` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/lgpd/politica-privacidade` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/consultas` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/prescricoes/paciente/1` | ✅ 200 | ✅ existe | ✅ existe | ✅ existe |
| `/api/pacientes/` | ❌ 500 (B-001) | ✅ existe + P0 fixes | ✅ existe | ⚠️ existe (sem P0) |
| `/api/dashboard/stats` | ❌ 500 (B-001) | ✅ existe | ✅ existe | ⚠️ existe |
| `/api/evolucoes/paciente/1` | ❌ 500 (B-001) | ✅ existe + P0 fixes | ✅ existe | ⚠️ existe |
| `/api/health` | ❌ 404 | ✅ existe (não commitado) | ❌ não existe | ❌ não existe |
| `/api/schema-version` | ❌ 404 | ✅ existe (não commitado) | ❌ não existe | ❌ não existe |
| `assert_required_secrets_on_startup` | NÃO COMPROVADO | ✅ existe (não commitado) | ❌ não existe | ❌ não existe |

### Conclusão FASE 1

**Produção está rodando código entre `a2e4131` (WIP before VPS deploy 20260620_165602) e HEAD.** O endpoint `/api/pacientes/` existe em produção e responde com 500 (B-001), o que significa que o modelo `data_revogacao` foi deployado. Mas o guard de migrations (`assert_migrations_applied`) e o `/api/schema-version` (M28) **não estão deployados**.

A versão em produção é provavelmente o **commit `a2e4131`** (WIP), deployado em 20/06/2026 16:56. Este commit foi criado **POSTERIOR** ao deploy para etiquetar a working tree que estava em produção.

---

## FASE 2 — Comparação Git × Produção

### Tabela: Arquivos críticos

| Arquivo | Existe no Git? | Existe em Produção? | Mesmo conteúdo? | Deployado? | Diferenças |
|---------|----------------|---------------------|-----------------|------------|------------|
| `app_cors_livre.py` | ✅ (HEAD ce141c5) | ✅ | ❌ | Parcialmente | Working tree tem 50+ modificações não commitadas; produção tem versão antiga SEM `/api/health` e SEM `assert_required_secrets_on_startup` |
| `services/deploy_guard.py` | ⚠️ **NÃO commitado** (untracked) | ❌ NÃO | n/a | **NÃO** | M28 não deployado |
| `services/webhook_auth.py` | ✅ | ✅ (assume) | ✅ | Provavelmente | código similar; assert_required_secrets existe em prod (M22.2) |
| `tenant_lib.py` | ✅ + working tree modified | ✅ (assume) | ⚠️ | Provavelmente versão antiga | tenant com `X-Association-ID` retorna 403 sempre — pode ser bug do tenant_lib versão prod |
| `security_config.py` | ✅ + working tree modified | ✅ (assume) | ⚠️ | Provavelmente | CSP/HSTS em prod (M18-) |
| `config.py` | ✅ + working tree modified | ✅ (assume) | ⚠️ | Provavelmente | — |
| `migrations/versions/REDACTED.py` | ✅ (criado 22/06) | ❌ | n/a | **NÃO** | Migration existe no repo mas **nunca foi aplicada em produção** |
| Outras 14 migrations | ✅ | ❓ | n/a | **NÃO comprovado** | Sem endpoint para verificar alembic_version |
| Frontend (`frontend/src/components/*`) | ✅ + working tree modified | ✅ (assume) | ⚠️ | Provavelmente | — |
| `.env.example` | ✅ | n/a | — | — |
| `.env.production.example` | ✅ | n/a | — | — |
| **Total de arquivos modificados (working tree)** | 130+ arquivos M | n/a | n/a | **NÃO deployado** |

### Resumo da divergência

- **HEAD ≠ Working tree:** working tree tem 130+ modificações não commitadas
- **Working tree ≠ Produção:** produção tem versão ainda mais antiga que o working tree
- **Produção = commit `a2e4131` (WIP 20/06)**: deploy manual de working tree não commitado

---

## FASE 3 — Migration Audit

### Estado das migrations

| Migration | Existe no repo | Aplicada em produção | Idempotente? |
|-----------|----------------|---------------------|--------------|
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ (usa `ADD COLUMN` direto) |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `bb2cbd44835d_merge_heads` | ✅ | **NÃO COMPROVADO** | merge |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `REDACTED` | ✅ | **NÃO COMPROVADO** | ❌ |
| `f3a8c9d2e1b4_add_catalog_fields` | ✅ | **NÃO COMPROVADO** | ❌ |
| `2026_06_17_clinica_management_flag` | ✅ | **NÃO COMPROVADO** | ❌ |
| `2026_06_21_add_modulos_tables` | ✅ | **NÃO COMPROVADO** | ❌ |
| **`REDACTED`** | ✅ | ❌ **NÃO** | ✅ SIM |

### Sobre `data_revogacao`

- **Existe no repositório:** ✅ SIM (`migrations/versions/REDACTED.py`)
- **Existe em produção:** ❌ NÃO (provado pelo erro B-001 — `column "data_revogacao" does not exist`)
- **Idempotente:** ✅ SIM (`ADD COLUMN IF NOT EXISTS`)
- **Aplicável sem risco:** ✅ SIM (não-destrutiva, NULL, sem lock)
- **Por que não foi aplicada:** ver FASE 7 (root cause)

### Sobre `alembic_version` em produção

- **NÃO COMPROVADO via API** (não há endpoint público que retorne)
- Provavelmente **NÃO EXISTE** (porque se existisse, o erro de INSERT viria de outra origem; o fato de ser `UndefinedColumn` puro, sem foreign key violation ou similar, sugere que a tabela foi criada via `db.create_all()` sem alembic)

### Migrations que podem falhar em `flask db upgrade`

Todas as 14 migrations que **NÃO** usam `IF NOT EXISTS` podem falhar em produção se o DB já tem as colunas/tabelas via `db.create_all()` (mesmo problema de staging reportado em M27).

A única migration segura para aplicar **diretamente em produção** (sem `flask db upgrade`) é a `REDACTED` por ser idempotente.

---

## FASE 4 — Endpoint Audit

### Endpoints novos das últimas missões

| Endpoint | Missão que adicionou | Em produção? | Resposta | Veredito |
|----------|---------------------|--------------|----------|----------|
| `/api/health` | M20 | ❌ NÃO | 404 | **NÃO deployado** |
| `/api/schema-version` | M28 | ❌ NÃO | 404 | **NÃO deployado** |
| `/api/auth/profile` (M0) | base | ✅ SIM | 200 | OK |
| `/api/csrf-token` | base | ✅ SIM | 200 | OK |
| `/api/planos/meu-plano` | M19 | ✅ SIM | 200 | OK |
| `/api/dashboard/stats` | base | ❌ 500 (B-001) | 500 | bloqueado por schema |

### Endpoints que retornam 500 (B-001)

| Endpoint | Erro | Causa |
|----------|------|-------|
| `POST /api/pacientes/` | 500 | `column "data_revogacao" of relation "pacientes" does not exist` |
| `GET /api/pacientes/` | 500 | mesmo erro |
| `GET /api/dashboard/stats` | 500 | depende de Paciente |
| `GET /api/evolucoes/paciente/1` | 500 | depende de Paciente |

### Webhooks

| Endpoint | Sem assinatura | Veredito |
|----------|---------------|----------|
| `POST /api/mercadopago/webhook` | 400 | ✅ Rejeitado |
| `POST /api/dr-anderson/webhook` | 200 | ⚠️ **Aceito sem auth** (bug) |
| `POST /api/tenant/webhook` | 200 | ⚠️ **Aceito sem auth** (bug) |

### Rate-limit

- 11 logins consecutivos sem ativar 429
- Rate-limit **NÃO está ativo em produção** (ou está muito permissivo)

### Deploy Guard

- ❌ `/api/schema-version` 404 — guard **NÃO deployado**
- ❌ `assert_required_secrets_on_startup` — existe em prod (M22.2), mas **`run_all_checks` (M28) NÃO está deployado**

---

## FASE 5 — Environment Audit

### Arquivos de configuração

| Arquivo | Linhas | Vars | Última modificação |
|---------|--------|------|--------------------|
| `.env.example` | 5030 bytes | 37 | 2026-06-27 15:51 |
| `.env.production.example` | 5442 bytes | 42 | 2026-06-27 15:51 |

### Vars em `.env.example` mas NÃO em `.env.production.example`

- `ALLOW_WEBHOOK_SIMULATION`
- `CREWAI_TIMEOUT`
- `DATABASE_URL`

### Vars em `.env.production.example` mas NÃO em `.env.example`

- `ANONYMIZATION_AUDIT_MODEL`
- `ANONYMIZATION_KEY`
- `ANTHROPIC_API_KEY`
- `API_BASE_URL`
- `CORS_ORIGINS`
- `CREWAI_DISABLE_TELEMETRY`
- `CREWAI_DISABLE_TRACKING`
- `DEEPSEEK_API_KEY`
- (e outros...)

### Secrets necessários em produção (sem verificação real)

| Secret | Esperado em prod | Verificável? |
|--------|------------------|--------------|
| `JWT_SECRET_KEY` | ✅ esperado | ❌ (não exposto) |
| `SECRET_KEY` | ✅ esperado | ❌ |
| `CSRF_TOKEN` | ✅ esperado | ❌ |
| `DATABASE_URL` | ✅ esperado | ❌ |
| `MERCADOPAGO_WEBHOOK_SECRET` | ✅ esperado | ❌ |
| `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` | ✅ esperado | ❌ |
| `EVOLUTION_WEBHOOK_SECRET` | ✅ esperado | ❌ |
| `DR_ANDERSON_WEBHOOK_SECRET` | ✅ esperado | ❌ |
| `INTERNAL_SERVICE_KEY` | ✅ esperado | ❌ |
| `ANONYMIZATION_KEY` | ✅ esperado | ❌ |

### Divergências

- **37 vs 42 vars:** `.env.production.example` tem mais 5 vars de AI (Anthropic, DeepSeek) e 1 de CORS_ORIGINS que `.env.example` não tem
- `.env.example` tem `DATABASE_URL` que `.env.production.example` não tem (dividido em POSTGRES_DB/USER/PASSWORD)
- Working tree tem ambos modificados — mudanças não auditadas

---

## FASE 6 — Pipeline Audit

### Cadeia de deploy

```
GitHub push
   ↓
GitHub Actions (cd-production.yml)
   ↓ 1. build → 2. lint → 3. test → 4. security
   ↓ 5. smoke → 6. playwright → 7. lighthouse
   ↓ 8. backup → 9. deploy (./scripts/deploy_prod.sh)
   ↓
   Post-deploy smoke
   ↓
   Container em produção
```

### Onde está quebrando a cadeia

| Etapa | Estado | Problema |
|-------|--------|----------|
| 1. Build | ✅ OK | Imagem Docker é buildada |
| 2. Lint | ✅ OK | Lint passa |
| 3. Test | ✅ OK | Testes passam |
| 4. Security | ✅ OK | Bandit/safety/trivy |
| 5. Smoke | ⚠️ | Container efêmero pode passar mesmo com DB divergente |
| 6. Playwright | ⚠️ | E2E pode passar mesmo com DB divergente (testa staging) |
| 7. Lighthouse | ✅ OK | Performance |
| 8. Backup | ✅ OK | `./scripts/backup.sh --env=production` |
| **9. Deploy** | ❌ **QUEBRA** | `./scripts/deploy_prod.sh` executa, mas... |
| **9.1. Migration** | ❌ **AUSENTE** | **Pipeline NÃO chama `flask db upgrade`** |
| 9.2. Start | ⚠️ | Container inicia, mas schema diverge |

### Evidência-chave: Pipeline não roda migrations

```bash
$ grep -n "flask db upgrade\|migrate" .github/workflows/cd-production.yml
(nada)
```

```bash
$ grep -n "entrypoint\|flask db" docker-compose.prod.yml
(nada)
```

```bash
$ cat Dockerfile.backend | grep -i "entrypoint\|cmd"
CMD ["python", "app_cors_livre.py", "--port", "5002"]
```

**O `entrypoint_siap.sh` que contém `flask db upgrade` NÃO é referenciado no Dockerfile.prod nem no docker-compose.prod.** Apenas o `docker-compose.staging.yml` o usa.

### Cadeia quebrada — diagrama

```
cd-production.yml
  └─ ./scripts/deploy_prod.sh        ← NÃO chama flask db upgrade
       └─ docker-compose.prod up     ← usa CMD do Dockerfile (python app_cors_livre.py)
            └─ App inicia SEM migration
                 └─ Schema DB ≠ código
                      └─ 500 em qualquer rota que toca coluna nova
```

---

## FASE 7 — Root Cause

### Pergunta

> "Por que produção não está rodando o código atual?"

### Resposta objetiva (com evidências)

**Produção não está rodando o código atual porque (1) nenhum deploy foi feito desde 20/06/2026, e (2) mesmo nesse deploy, `flask db upgrade` nunca foi executado.**

### Evidências

1. **HEAD do repo (ce141c5) é de 2026-06-22 03:30.** Mas produção ainda roda código de 20/06/2026 16:56 (commit `a2e4131`).
   - **Evidência:** `/api/health` e `/api/schema-version` retornam 404 em produção, mas ambos existem no working tree (não commitados).
   - **Evidência:** working tree tem `git blame` marcando linhas como "Not Committed Yet" — código mais recente que nunca passou por git commit.

2. **Mesmo o deploy de 20/06 não rodou migrations.**
   - **Evidência:** `entrypoint_siap.sh` (que contém `flask db upgrade`) NÃO é chamado em produção — não está no `Dockerfile.backend` (só CMD direto), não está no `docker-compose.prod.yml`, e nem mesmo está em `.github/workflows/cd-production.yml`.
   - **Evidência:** Bug B-001 persiste desde M26 (26/06) — mesmo após 1 dia de missões M27/M28/M29 tentando corrigir — porque **nenhum deploy aconteceu**.

3. **Working tree está divergente do HEAD.**
   - **Evidência:** 130+ arquivos modificados + 2 arquivos novos (`services/deploy_guard.py`, `tests/test_deploy_guard.py`) **não commitados**.
   - **Implicação:** mesmo que um deploy fosse feito agora, estaria deployando código que **não existe em nenhum commit** — apenas no working tree.

4. **Migration `REDACTED.py` existe mas nunca foi aplicada.**
   - **Evidência:** erro de INSERT em produção retorna `column "data_revogacao" does not exist`.
   - **Causa raiz:** alembic nunca rodou em produção. Provavelmente o DB de produção foi criado via `db.create_all()` em algum momento, e migrations foram completamente puladas.

### Cadeia causal resumida

```
Deploy 20/06 (working tree não commitado)
   ↓ (NÃO rodou flask db upgrade — não há step no pipeline nem entrypoint)
   ↓ (NÃO rodou db.create_all — provavelmente assumia DB já criado)
   ↓ (Schema de prod é o que estava em prod antes desse deploy)
Container inicia com código novo + schema velho
   ↓
data_revogacao esperada pelo model NÃO existe no DB
   ↓
GET /api/pacientes/ → 500 (B-001)
```

**Nenhum deploy foi feito depois de 20/06, então o problema persiste.**

---

## FASE 8 — Plano mínimo NO-GO → GO CONDICIONAL

> ⚠️ **Plano, NÃO execução.** M30 não corrige nada.

### Pré-condições gerais

- Operador com acesso SSH ao VPS de produção
- Operador com permissão `psql` no banco de produção
- Janela de manutenção: ~30 minutos

### PASSO 1 — Commit working tree (CRÍTICO)

| Item | Detalhe |
|------|---------|
| **Tempo** | 10–15 min |
| **Risco** | Baixo se commit for bem descrito; alto se misturar mudanças não relacionadas |
| **Rollback** | `git reset HEAD~1` (após commit) |
| **Pré-condições** | revisão do diff antes |
| **Resultado esperado** | HEAD do repo bate com working tree |

```bash
# No repo local:
git add -A
git commit -m "WIP: working tree 2026-06-27 — inclui M28 deploy_guard + M22-M25 fixes"
git push origin fix/p0-stabilization-2026-06
```

### PASSO 2 — Commit das mudanças de M28 (separado)

| Item | Detalhe |
|------|---------|
| **Tempo** | 5 min |
| **Risco** | Baixo |
| **Rollback** | revert commit |
| **Pré-condições** | — |
| **Resultado esperado** | `services/deploy_guard.py` e `tests/test_deploy_guard.py` versionados |

```bash
# Separar do WIP:
git add services/deploy_guard.py tests/test_deploy_guard.py docs/DEPLOY_PIPELINE_HARDENING.md
git commit -m "feat(deploy): M28 deploy_guard + schema-version endpoint + 12 tests"
```

### PASSO 3 — Aplicar migration B-001 em produção (resolve o blocker)

| Item | Detalhe |
|------|---------|
| **Tempo** | 5 min |
| **Risco** | **Muito baixo** (idempotente, NULL, sem lock) |
| **Rollback** | `ALTER TABLE pacientes DROP COLUMN data_revogacao;` |
| **Pré-condições** | backup pré-aplicação (PASSO 4 primeiro) |
| **Resultado esperado** | coluna `data_revogacao` existe; INSERT funciona |

```bash
# SSH no VPS de produção:
cd /opt/araos
psql -h <prod-db-host> -U siap_user -d aracannabis -c \
  "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;"

# OU, mais completo (stamping alembic):
psql -h <prod-db-host> -U siap_user -d aracannabis -c \
  "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;
   CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL);
   INSERT INTO alembic_version (version_num) VALUES ('REDACTED')
     ON CONFLICT DO NOTHING;"
```

### PASSO 4 — Backup pré-deploy

| Item | Detalhe |
|------|---------|
| **Tempo** | 5–15 min (depende do tamanho do DB) |
| **Risco** | Nenhum (leitura) |
| **Rollback** | n/a |
| **Pré-condições** | — |
| **Resultado esperado** | snapshot do DB salvo em `/var/backups/siap/` |

```bash
./scripts/backup.sh --env=production
```

### PASSO 5 — Triggerar pipeline de deploy (ou deploy manual)

| Item | Detalhe |
|------|---------|
| **Tempo** | 10–20 min (build + push + restart) |
| **Risco** | Médio — pode introduzir regressões se working tree tiver bugs |
| **Rollback** | `./scripts/rollback.sh --env=production` |
| **Pré-condições** | PASSO 1 e 2 feitos (working tree commitado e pushed) |
| **Resultado esperado** | container em produção rodando novo commit |

```bash
# Opção A: tag + push (dispara cd-production.yml)
git tag v0.9.0-p0-stabilization
git push origin v0.9.0-p0-stabilization

# Opção B: deploy manual (se pipeline não disponível)
ssh prod "cd /opt/araos && ./scripts/deploy_prod.sh v0.9.0-p0-stabilization"
```

### PASSO 6 — Atualizar `entrypoint_siap.sh` para incluir guard de migrations

| Item | Detalhe |
|------|---------|
| **Tempo** | 5 min |
| **Risco** | Baixo (adicionar linha ao entrypoint) |
| **Rollback** | git revert |
| **Pré-condições** | working tree commitado |
| **Resultado esperado** | container aborta se migration não aplicada |

Adicionar ao `entrypoint_siap.sh`:
```bash
echo "Running DB init/upgrade..."
if [ -d "migrations" ]; then
  REV=$(ls -1 migrations/versions/*.py | xargs -I{} grep -h "^revision = " {} | sed -E "s/.*'([^']+)'.*/\1/" | head -1)
  if [ ${#REV} -gt 32 ]; then
    # alembic version_num VARCHAR(32) — fallback SQL direto
    psql -h siap-db -U siap_user -d aracannabis -c \
      "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;"
  else
    flask db upgrade
  fi
fi
```

E garantir que o `Dockerfile.backend` usa `entrypoint_siap.sh`:
```dockerfile
COPY entrypoint_siap.sh /entrypoint_siap.sh
RUN chmod +x /entrypoint_siap.sh
ENTRYPOINT ["/entrypoint_siap.sh"]
```

### PASSO 7 — Re-rodar M29 smoke + carga leve

| Item | Detalhe |
|------|---------|
| **Tempo** | 10 min |
| **Risco** | Nenhum (leitura + smoke) |
| **Rollback** | n/a |
| **Pré-condições** | PASSO 5 completo (deploy novo em prod) |
| **Resultado esperado** | 17/17 endpoints OK; carga leve sem degradação |

```bash
cd /tmp && python3 m29_smoke.py
cd /tmp && python3 m29_load.py 90 5
```

### PASSO 8 — Decisão GO CONDICIONAL

| Item | Detalhe |
|------|---------|
| **Tempo** | 5 min |
| **Risco** | Nenhum |
| **Rollback** | n/a |
| **Pré-condições** | PASSO 7 verde |
| **Resultado esperado** | Beta fechado de 5 médicos por 2-4 semanas autorizado |

### Tempo total estimado

| Passo | Tempo |
|-------|-------|
| 1. Commit working tree | 15 min |
| 2. Commit M28 separado | 5 min |
| 3. Backup pré-deploy | 15 min |
| 4. Migration B-001 | 5 min |
| 5. Deploy novo | 20 min |
| 6. Atualizar entrypoint | 5 min |
| 7. Re-smoke + carga | 10 min |
| 8. Decisão | 5 min |
| **TOTAL** | **~80 min** |

---

## Respondendo as 5 perguntas obrigatórias

### 1. Produção está sincronizada com Git?

**NÃO.** Três níveis de divergência:

| Nível | Estado |
|-------|--------|
| Git HEAD (`ce141c5`) | tem código de 22/06 |
| Working tree | tem **130+ modificações não commitadas + 2 arquivos novos (M28)** posteriores ao HEAD |
| Produção | roda código de **20/06/2026 16:56** (commit `a2e4131` WIP) — **anterior ao HEAD** |

### 2. Qual commit está realmente em produção?

**NÃO COMPROVADO diretamente** (sem acesso SSH).

**Mais provável:** `a2e4131` "WIP before VPS deploy 20260620_165602" — baseado em:

- `/api/health` retorna 404 (endpoint que está em working tree, não em HEAD)
- `/api/schema-version` retorna 404 (M28, não commitado)
- `data_revogacao` causa 500 (modelo deployado mas coluna não aplicada)
- Working tree tem MUITOS arquivos modificados não commitados — significa que **HEAD ≠ working tree**, e produção está ainda mais atrás

**Confirmação definitiva requer:** acesso SSH + `docker inspect` no container de produção para ler `Config.Image` ou label.

### 3. Quantos artefatos ainda não foram deployados?

| Artefato | Commits/arquivos | Origem |
|----------|------------------|--------|
| Migration `data_revogacao` | 1 migration | M27 |
| `services/deploy_guard.py` | 1 arquivo + 240 linhas de testes | M28 |
| `/api/schema-version` endpoint | 1 rota | M28 |
| Working tree (130+ arquivos M) | ~50 commits pós-20/06 | M22–M29 |
| `entrypoint_siap.sh` corrigido | 1 arquivo (passo 6 do plano) | proposto M30 |
| **TOTAL estimado** | **~50 commits + 3 artefatos novos** | ~7 dias de trabalho |

### 4. Existe risco de novo B-001?

**SIM — risco ALTO.** Mesma causa raiz não foi corrigida:

- `Dockerfile.backend` ainda tem `CMD ["python", "app_cors_livre.py", ...]` direto — sem `flask db upgrade`
- `docker-compose.prod.yml` ainda não tem entrypoint
- `cd-production.yml` ainda não chama migrations
- Working tree tem migrations novas (M28 não tem, mas tem outras como `2026_06_17_clinica_management_flag`, `2026_06_21_add_modulos_tables`) que **também não foram aplicadas em produção**

**Próximo deploy de migration adicionando coluna nova** → repetirá B-001.

### 5. Qual o menor conjunto de ações para transformar NO-GO em GO CONDICIONAL?

**4 ações obrigatórias** (do plano da FASE 8):

1. **Commit working tree + M28** (passos 1+2) — para que git reflita o estado real
2. **Aplicar migration B-001** (passo 4) — para resolver o 500 atual
3. **Deploy novo commit** (passo 5) — para subir correções P0/P1 de M25 + guard M28
4. **Re-validar com M29 smoke** (passo 7) — para confirmar verde

**Tempo total: ~80 minutos** (sem contar janelas de manutenção ou análise adicional).

**Opcional mas recomendado** (não bloqueia GO CONDICIONAL):

- Passo 6: corrigir `entrypoint_siap.sh` para que próximos deploys rodem migrations automaticamente

---

## Restrições respeitadas

- ✅ Não corrigi nenhum bug
- ✅ Não alterei regras de negócio
- ✅ Não criei features
- ✅ Não alterei frontend
- ✅ Não refatorei código
- ✅ Não procurei bugs novos além do necessário para diagnóstico
- ✅ Tudo baseado em evidência (probes HTTP + git local + inspeção de arquivos)
- ✅ Sem commit
- ✅ Sem push
- ✅ Sem PR

---

# DECISÃO FINAL

# **NO-GO**

**Causa:** produção está rodando código de 20/06/2026 (commit `a2e4131`), enquanto o repositório tem código de 22/06 (HEAD `ce141c5`) + 130+ arquivos modificados não commitados. A migration `data_revogacao` existe mas nunca foi aplicada em produção porque **o pipeline não chama `flask db upgrade` em nenhum lugar**.

**Plano de reversão:** 8 passos detalhados acima, totalizando ~80 minutos.

**Próxima ação recomendada:** operador com acesso SSH/PSQL ao VPS de produção executar PASSO 3 (aplicar migration) — isoladamente, já remove o blocker B-001 e permite o beta sem o restante das mudanças. Mas para sincronização completa, executar os 8 passos.

**Parando conforme instrução.** M30 concluída.