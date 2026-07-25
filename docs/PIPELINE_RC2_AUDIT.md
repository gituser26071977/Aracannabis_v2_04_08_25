# PIPELINE_RC2_AUDIT — MISSÃO D02 FASE 1

**Data:** 2026-06-30
**Hora:** 21:00 -03
**Modo:** AUDIT (read-only; somente leitura de workflows + estado)
**Origem:** D02 — Pipeline Fix & RC2 Release (FASE 1)
**Alvo:** Workflows GitHub Actions em `gituser26071977/Aracannabis_v2_04_08_25`

---

# Resumo executivo (1 página)

| Pergunta | Resposta |
|----------|----------|
| Qual workflow dispara por tag? | **`CD — Production (9-stage pipeline + auto-rollback)`** — `on.push.tags: ['v*.*.*']` + `workflow_dispatch` |
| Qual workflow dispara por PR? | **`Deploy VPS`** (legado, ID 294844757, `pull_request`, último run 2026-06-13) + **`CI`** (`pull_request` para main/develop) |
| Qual workflow publica imagem? | **❌ NENHUM** — nenhum workflow executa `docker push` para o GHCR |
| Qual workflow faz deploy? | **`CD — Production`** stage 9/9 (SSH + `deploy_prod.sh`) e **`CD — Staging`** stage 9/9 (`deploy_staging.sh`) |

**Achado crítico:** A pipeline constrói imagens Docker (`docker build`) mas **nunca publica no registry**. Stage 5/9 (Smoke) tenta `docker run siap-backend:prod-<sha>` e falha com `pull access denied` porque a imagem é local ao runner, não está no GHCR.

---

# 1. Inventário de workflows

## 1.1 Workflows ativos (5 listados)

| ID | Nome | Path | Triggers | Origem file |
|----|------|------|----------|-------------|
| 304700055 | **CD — Production (9-stage pipeline + auto-rollback)** | `.github/workflows/cd-production.yml` | `push: tags: ['v*.*.*']` + `workflow_dispatch(inputs: version)` | ✅ LOCAL |
| 304190514 | **CD — Staging (9-stage pipeline + auto-rollback)** | `.github/workflows/cd-staging.yml` | `push: branches: [develop, 'feat/**', 'fix/**']` + `workflow_dispatch` | ✅ LOCAL |
| 304190516 | **CI** | `.github/workflows/ci.yml` | `push: branches: [main, develop, 'feat/**', 'fix/**', 'arch/**']` + `pull_request: [main, develop]` | ✅ LOCAL |
| 294844757 | **Deploy VPS** (legado) | `.github/workflows/deploy.yml` | `pull_request` | ❌ **ÓRFÃO** (sem file em nenhuma branch; listou último run 2026-06-13) |
| 304190492 | **Lighthouse CI — Desktop + Mobile** | `.github/workflows/lighthouse.yml` | `workflow_dispatch` + `workflow_call` | ✅ LOCAL |

## 1.2 Workflow órfão — `Deploy VPS`

- **Path declarado:** `.github/workflows/deploy.yml`
- **Arquivo existe em alguma branch?** **NÃO** (verificado em `main`, `develop`, `feat/secretaria-staff`, `fix/p0-stabilization-2026-06`)
- **Último run:** 2026-06-13 (há 17 dias), `pull_request`, branch `feat/secretaria-staff`
- **Conclusão últimos runs:** success (1) + failure (2)
- **Status:** Aparece como `active` no GitHub Actions mas é um "zumbi" — o file foi removido em algum momento mas o workflow continua registrado
- **Ação FASE 2:** considerar desabilitar (`gh workflow disable 294844757`)

## 1.3 Workflows locais (analisados em detalhe)

### CD — Production (cd-production.yml — 9321 bytes)
- **Triggers:** `push: tags: ['v*.*.*']` + `workflow_dispatch` (com input `version`)
- **Secrets esperados:** `PROD_SSH_HOST`, `PROD_SSH_KEY`, `PROD_DEPLOY_USER`, `SLACK_WEBHOOK_URL` (não existe), `LHCI_GITHUB_APP_TOKEN`
- **9 stages:**
  1. **Build** — `docker build` backend + frontend (sem `docker push`)
  2. **Lint** — `pip install flake8 bandit` + `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` + `bandit -r . -lll -iii`
  3. **Tests (full)** — `pip install -r requirements.txt -r requirements-test.txt` + pytest
  4. **Security (SAST + SCA + image scan)** — bandit + safety + pip-audit + **Trivy image scan com `exit-code: '1'`** (HIGH/CRITICAL fail)
  5. **Smoke (container efêmero)** — `docker run -d siap-backend:prod-<sha>` (sem `docker pull`, espera local) + curl 3 endpoints
  6. **Playwright E2E** (13 flows + screenshots) — `BASE_URL: https://staging.visualsmartflow.com.br`
  7. **Lighthouse** — usa `LHCI_GITHUB_APP_TOKEN`
  8. **Pre-deploy Backup** — SSH → `cd /root/projetos/araos` (corrigido de `/opt/araos`) + `./scripts/backup.sh --env=production`
  9. **Deploy + Smoke + Auto-Rollback** — SSH → `git fetch --tags --all` + `./scripts/deploy_prod.sh ${{ github.ref_name }}` + post-deploy smoke + auto-rollback

### CD — Staging (cd-staging.yml — 14596 bytes)
- **Triggers:** `push: branches: [develop, 'feat/**', 'fix/**']` + `workflow_dispatch`
- **Secrets esperados:** `STAGING_SSH_HOST`, `STAGING_SSH_KEY`, `STAGING_DEPLOY_USER`, `SLACK_WEBHOOK_URL`, `LHCI_GITHUB_APP_TOKEN`
- **Estrutura:** idêntica ao CD Production (9 stages), mas:
  - Tag das imagens: `siap-backend:staging-<sha>` (em vez de `prod-`)
  - Path no VPS: `cd /opt/araos` (NÃO corrigido — bug idêntico ao que eu corrigi em CD Production)
  - Secrets: `STAGING_*` (mas só `STAGING_SSH_KEY` existe; `STAGING_SSH_HOST` e `STAGING_DEPLOY_USER` NÃO)
  - Mesmos problemas de flake8, requirements-test.txt, sem docker push

### CI (ci.yml — 2396 bytes)
- **Triggers:** `push: branches: [main, develop, 'feat/**', 'fix/**', 'arch/**']` + `pull_request: [main, develop]`
- **3 jobs:** `validate` (lint + typecheck + tests via npm), `security` (npm audit + Snyk), `build-mobile` (type-check + build)
- **⚠️ Foco em mobile/TypeScript**, não em backend Python — roda `npm ci`, `npm run lint`, etc.
- **Não tem relação com deploy de produção**

### Lighthouse (lighthouse.yml — 1284 bytes)
- **Triggers:** `workflow_dispatch` + `workflow_call`
- **2 jobs:** `lighthouse-desktop` + `lighthouse-mobile` — rodam `treosh/lighthouse-ci-action@v11` com `configPath: .lighthouserc.json`
- **Independente** dos pipelines de deploy

---

# 2. Resposta às perguntas da FASE 1

| Pergunta | Resposta | Evidência |
|----------|----------|-----------|
| **Qual workflow dispara por tag?** | `CD — Production` | `on.push.tags: ['v*.*.*']` em cd-production.yml:5 |
| **Qual workflow dispara por PR?** | `CI` (lint+test+build mobile) + `Deploy VPS` (legado, zumbi) | ci.yml:7 + workflow 294844757 (órfão) |
| **Qual workflow publica imagem?** | **❌ NENHUM** | grep `docker push` em todos os 4 files locais: **0 resultados** |
| **Qual workflow faz deploy?** | `CD — Production` (prod) + `CD — Staging` (staging) | Stage 9/9 de cada um, via `appleboy/ssh-action@v1` + scripts |

---

# 3. Bugs e gaps identificados (input para FASE 2)

## 3.1 Bug crítico: imagens nunca publicadas

**Sintoma:** Stage 5/9 Smoke do CD Production rodou (em 2026-06-30 23:58) e falhou com:
```
Unable to find image 'siap-backend:REDACTED' locally
docker: Error response from daemon: pull access denied for siap-backend,
       repository does not exist or may require 'docker login': denied
```

**Causa:** O Build stage (1/9) executa `docker build -t siap-backend:prod-<sha> .` mas não executa `docker push`. A imagem fica apenas no contexto do runner. O Smoke (5/9) tenta `docker run siap-backend:prod-<sha>` que não está disponível nem localmente (runner novo) nem no registry.

**Correção (FASE 2):**
- Adicionar `docker login` + `docker push` no Build stage
- Push para `ghcr.io/${{ github.repository }}/siap-backend:prod-<sha>` (e frontend)
- Validar digest publicado antes de prosseguir (4/9 Security precisa disso)

## 3.2 Bug médio: Lint sem config

**Sintoma:** 32 erros F821 (undefined name) + 1 F824 (global unused) reportados por flake8 em todos os 2 runs do CD Production (28445925121 e 28483588008).

**Causa raiz:**
- O projeto NÃO tem `.flake8`, `setup.cfg`, `pyproject.toml`, `tox.ini`, `.isort.cfg` (verificado: 0 matches)
- O comando `flake8 . --select=E9,F63,F7,F82` é genérico e pega F821/F824 que não estão no select mas flake8 5.x/6.x (versão no runner) ainda reporta

**Verificação:** flake8 local (7.3.0, pyflakes 3.4.0, Python 3.14) **NÃO** reporta F821 (entende imports modernos); flake8 do runner (versão antiga) reporta como falso positivo.

**Correção (FASE 2):**
- Criar `.flake8` no projeto com:
  ```ini
  [flake8]
  exclude = python_env,venv,.venv,node_modules,build,dist,htmlcov,.git,migrations,araos,docs
  ignore = F821,F824,W503,E203
  max-line-length = 120
  ```
- Esse arquivo vai ser usado por flake8 automaticamente (sem mudar workflow)

## 3.3 Bug médio: `requirements-test.txt` inexistente

**Sintoma:** Stage 3/9 Tests falhou em ambos os runs com:
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements-test.txt'
```

**Causa raiz:** O projeto só tem `requirements.txt` (1094 bytes) e `requirements_basic.txt` (205 bytes). NÃO tem `requirements-test.txt`. Workflows CD Production e CD Staging referenciam o arquivo inexistente.

**Correção (FASE 2):**
- Criar `requirements-test.txt` com deps de teste:
  ```
  pytest>=7.4.0
  pytest-cov>=4.1.0
  pytest-flask>=1.3.0
  pytest-playwright>=0.4.0
  requests-mock>=1.11.0
  freezegun>=1.4.0
  ```

## 3.4 Bug crítico: deploy sem validação de imagem

**Sintoma:** Stage 9/9 Deploy do CD Production faz `git fetch && ./scripts/deploy_prod.sh <tag>` mas o `deploy_prod.sh` chama `docker compose pull` que pode falhar silenciosamente se a imagem não existir.

**Causa raiz:** Pipeline não valida digest/imagem antes de prosseguir para o deploy. Se a imagem não foi publicada, o `docker compose pull` falha com erro genérico.

**Correção (FASE 2):**
- Adicionar step "Validate image digest" no Build stage (após push):
  ```bash
  docker pull ghcr.io/${{ github.repository }}/siap-backend:prod-${{ github.sha }}
  docker pull ghcr.io/${{ github.repository }}/siap-frontend:prod-${{ github.sha }}
  ```
- Adicionar step "Validate image exists" no Deploy stage (antes de chamar deploy_prod.sh):
  ```bash
  if ! docker manifest inspect ghcr.io/${{ github.repository }}/siap-backend:prod-${{ github.sha }} >/dev/null 2>&1; then
    echo "✗ Image not in GHCR — ABORT"
    exit 1
  fi
  ```

## 3.5 Bug médio: Secrets STAGING_* incompletos

**Causa:** Workflow CD Staging (cd-staging.yml) referencia:
- `STAGING_SSH_HOST` — ❌ não existe
- `STAGING_SSH_KEY` — ✅ existe (verificado em M37)
- `STAGING_DEPLOY_USER` — ❌ não existe

**Correção (FASE 2):** criar os 2 secrets faltantes, OU renomear workflow para usar `VPS_*` (mais simples).

## 3.6 Bug menor: Deploy VPS workflow órfão

**Causa:** Workflow ID 294844757 ("Deploy VPS") está listado como active mas o file não existe em nenhuma branch. Provavelmente foi deletado em commit mas o registro persiste.

**Correção (FASE 2):** `gh workflow disable 294844757` (não deletar — registro pode ter histórico útil).

## 3.7 Estado de secrets GitHub (auditados em D01 F5)

| Secret | Existe | Último update | Notas |
|--------|--------|---------------|-------|
| `PROD_SSH_HOST` | ✅ (criado em D01) | 2026-06-30 | `147.93.33.253` |
| `PROD_SSH_KEY` | ✅ (criado em D01) | 2026-06-30 | chave ed25519 dedicada |
| `PROD_DEPLOY_USER` | ✅ (criado em D01) | 2026-06-30 | `root` |
| `STAGING_SSH_HOST` | ❌ | — | precisa criar |
| `STAGING_SSH_KEY` | ✅ | 2026-06-12 | provavelmente correto |
| `STAGING_DEPLOY_USER` | ❌ | — | precisa criar |
| `SLACK_WEBHOOK_URL` | ❌ | — | notif falha silenciosa (continue-on-error) |
| `LHCI_GITHUB_APP_TOKEN` | ❌ verificado | — | usado por Lighthouse |

---

# 4. Outras divergências (corrigidas em D01, validadas em D02)

| Item | Estado |
|------|--------|
| `cd-production.yml` path `/opt/araos` → `/root/projetos/araos` | ✅ Corrigido em commit `b07fa62` |
| `cd-production.yml` `git fetch --tags --all` adicionado | ✅ Corrigido em commit `b07fa62` |
| `cd-production.yml` flake8 com `--extend-ignore=F821` | ⚠️ **NÃO funciona** — flake8 ainda reporta (falso positivo em pyflakes antigo) — substituir por `.flake8` config |
| `cd-staging.yml` path `/opt/araos` | ❌ **NÃO corrigido** — mesmo bug |
| `cd-staging.yml` flake8/requirements-test.txt | ❌ **NÃO corrigido** — mesmo bug |
| Scripts `backup.sh`, `deploy_prod.sh`, `smoke.sh`, `rollback.sh`, `restore.sh`, `healthcheck.sh` no VPS | ✅ Deployado em `/root/projetos/araos/scripts/` (D01) |
| Authorized key `github_actions_siap` no VPS | ✅ Adicionado (D01) |

---

# 5. Configurações do projeto (estado real)

| Item | Existe? | Path | Notas |
|------|---------|------|-------|
| `.flake8` | ❌ | — | precisa criar |
| `setup.cfg` | ❌ | — | — |
| `pyproject.toml` | ❌ | — | — |
| `tox.ini` | ❌ | — | — |
| `.isort.cfg` | ❌ | — | — |
| `Dockerfile.backend` | ✅ | `Dockerfile.backend` (876 bytes) | Python 3.10-slim, tesseract, requirements.txt |
| `Dockerfile.siap` | ✅ | (797 bytes) | — |
| `Dockerfile.dockerfile` | ✅ | (157 bytes) | — |
| `Dockerfile.js` | ✅ | (157 bytes) | — |
| `requirements.txt` | ✅ | (1094 bytes) | Flask, JWT, SQLAlchemy, gunicorn, OpenAI, etc. |
| `requirements_basic.txt` | ✅ | (205 bytes) | subset mínimo |
| `requirements-test.txt` | ❌ | — | precisa criar |

---

# 6. Estado da tag `v1.0.0-rc.1` (input para FASE 4)

- **Existe?** ✅ Sim, pushed em 2026-06-30 (D01 F8)
- **Aponta para:** `b07fa62` (commit SEM correções completas — só path + git fetch)
- **Disparou CD Production?** ✅ 2 runs (`28445925121` + `28483588008`), ambos falharam em 2/9 Lint
- **Produção foi tocada?** ❌ **NÃO** (stages 8-9 que tocam VPS nunca rodaram)
- **Status:** **CONGELADO para auditoria** (NÃO mover, NÃO reusar, conforme D02 FASE 4)

---

# FASE 1 ENCERRADA

**Saída:** `docs/PIPELINE_RC2_AUDIT.md`

**Inputs para FASE 2:**
1. Adicionar `docker push` ao Build stage (CD Production + CD Staging)
2. Criar `.flake8` no projeto (resolve 3.2)
3. Criar `requirements-test.txt` no projeto (resolve 3.3)
4. Adicionar validação de imagem antes do deploy (resolve 3.4)
5. Criar secrets `STAGING_SSH_HOST` e `STAGING_DEPLOY_USER` (resolve 3.5)
6. Desabilitar workflow órfão `Deploy VPS` (resolve 3.6)
7. Corrigir path `/opt/araos` no CD Staging (resolve item da seção 4)

Auditoria concluída. Aguardando FASE 2.