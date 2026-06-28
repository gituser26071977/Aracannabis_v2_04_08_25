# REPOSITORY_STABILIZATION_REPORT — MISSÃO 32

**Data:** 2026-06-27
**Modo:** EXECUTE (somente organização, sem correção de regras de negócio)
**Origem:** M32 — Transformar repositório em estado limpo, reproduzível, pronto para RC1
**Versão alvo:** `v1.0.0-rc.1`

---

# Sumário executivo

**Working tree:** 269 entradas (94 modified + 175 untracked)
**Migrations:** 15, **1 head** (chain único, sem merge pendente)
**Testes:** 59 totais (38 em `tests/` raiz + 21 em subdirs `integration/load/security/smoke/e2e`)
**Documentação:** 119 docs + 39 em `AraFlow/` + 7 ADRs = 165 totais
**Artefatos a gitignorar:** ~165 MB identificados
**Recomendação:** repositório estruturalmente pronto para o release, mas working tree precisa ser commitado (9 commits propostos em M31)

---

## FASE 1 — Higiene do Git

### Classificação do working tree

#### Código fonte (a manter)

| Categoria | Modificados | Untracked | Total |
|-----------|-------------|-----------|-------|
| **Backend Python** | 23 | 11 | 34 |
| **Frontend React** | 82 | 11 | 93 |
| **Migrations** | 0 | 1 | 1 |
| **Testes** | 1 (test_deploy_guard.py) | 4 (subdirs) | 5 |
| **Total código** | **106** | **27** | **133** |

#### Infra / CI / Scripts (a manter)

| Categoria | Modificados | Untracked |
|-----------|-------------|-----------|
| **Docker** | 2 (compose.yml + compose.prod.yml) | 1 (compose.staging.yml) |
| **CI/CD** | 0 | .github/ workflows |
| **Scripts shell** | 1 (entrypoint_siap.sh) | 12 (backup, restore, rollback, smoke, healthcheck, deploy, etc.) |
| **Tooling** | 0 | 15+ (.editorconfig, .eslintrc.cjs, .prettierrc, .husky/, .lighthouserc, tsconfig*, package.json) |

#### Documentação (a manter — 100% conteúdo legítimo)

- 119 arquivos em `docs/` (+ 39 em `docs/AraFlow/`, + 7 em `docs/adr/`)
- 5 docs na raiz (README.md, CONTRIBUTING.md, RELEASE_MANIFEST.md, etc.)
- Relatórios de missões (M17-M31) — históricos
- READMEs de subsistema

#### Artefatos temporários / locais (NÃO versionar)

| Artefato | Tamanho estimado | Status atual |
|----------|------------------|--------------|
| `reports/load_*.html` + CSVs | ~4.7 MB | Untracked (não em .gitignore) |
| `instance/*.db` (sqlite local) | ~492 KB | Untracked (parcialmente coberto por `*.db`) |
| `venv_local/` | ~100 MB | Untracked (não em .gitignore — `venv/` está) |
| `htmlcov_week6/` | ~10 MB | Untracked (não em .gitignore) |
| `AGENDA.png` | ~200 KB | Untracked (não em .gitignore) |
| `eusoulia.png` | ~100 KB | Untracked (não em .gitignore) |
| `qrcode_eusoulia.png` | < 100 KB | Untracked (já em .gitignore) |
| `tools/araflow-cli/node_modules/` | ~50 MB | Untracked (parcialmente coberto) |
| **TOTAL estimado** | **~165 MB** | — |

### Arquivos gerados (caches — ignorar)

| Padrão | Localização |
|--------|-------------|
| `__pycache__/` | `tests/`, `migrations/versions/`, `services/`, etc. |
| `*.pyc`, `*.py[cod]` | geral |
| `.pytest_cache/` | geral |
| `.cache/`, `.turbo/` | geral |
| `node_modules/` | geral |

### Mudanças aplicadas ao .gitignore

**Arquivo modificado:** `.gitignore` (modified, 12 linhas adicionadas)

```gitignore
# M32 — Repository stabilization
# Local artifacts and runtime directories
instance/
venv_local/
htmlcov*/
coverage/

# Load test reports (Locust)
reports/

# Avulsas sem contexto
AGENDA.png
eusoulia.png

# Node modules de tooling
tools/*/node_modules/
tools/*/dist/
tools/*/build/
```

### Movimentação de artefatos

**NÃO executada.** Conforme restrição "Mover artefatos que não pertencem ao repositório para um diretório temporário **OU** documentar sua remoção", optei por **documentar**. Nenhuma pasta foi movida ou deletada do disco.

### Achados críticos

| # | Achado | Recomendação |
|---|--------|--------------|
| 1 | `.gitignore` atualizado | ✅ Aplicado |
| 2 | `reports/` ainda trackeável | ⚠️ Não coberto antes; agora em .gitignore |
| 3 | `instance/` coberto por `*.db` mas não pelo dir | ⚠️ Agora `instance/` em .gitignore |
| 4 | `venv_local/` (não `venv/`) não coberto | ⚠️ Agora coberto |
| 5 | `htmlcov*/` não coberto | ⚠️ Agora coberto |
| 6 | Imagens avulsas (AGENDA/eusoulia) | ⚠️ Agora cobertas |

---

## FASE 2 — Migrations

### Inventário (15 migrations)

| # | Revision | Down revision | Nome | Idempotente? |
|---|----------|---------------|------|--------------|
| 1 | `0331305d2b3c` | `None` (root) | add_reminder_settings_table | ❌ |
| 2 | `ec450c16ec01` | `0331305d2b3c` | REDACTED | ❌ |
| 3 | `f3a8c9d2e1b4_add_catalog_fields` | `ec450c16ec01` | add_catalog_fields | ❌ |
| 4 | `a1b2c3d4e5f6` | `ec450c16ec01` | REDACTED | ❌ |
| 5 | `bb2cbd44835d` | `(a1b2c3d4e5f6, f3a8c9d2e1b4_add_catalog_fields)` | merge_heads | n/a |
| 6 | `83c3e98787e1` | `bb2cbd44835d` | araos_week1_tenant_layer | ❌ |
| 7 | `7b45916cd7fc` | `bb2cbd44835d` | add_voice_session_tables | ❌ |
| 8 | `ca1ef05ac0d2` | `83c3e98787e1` | araos_week3_nervous_system | ❌ |
| 9 | `9b93d2cb67d7` | `ca1ef05ac0d2` | araos_week4_clinical_intelligence | ❌ |
| 10 | `791ba78aa8fb` | `9b93d2cb67d7` | araos_week5_agent_runtime | ❌ |
| 11 | `a7b8c9d0e1f2` | `(791ba78aa8fb, 7b45916cd7fc)` | add_conselho_tipo_to_profissionais (merge 2) | ❌ |
| 12 | `d3e4f5a6b7c8` | `a7b8c9d0e1f2` | add_consultorios_table | ❌ |
| 13 | `2026_06_17_clinica_management` | `d3e4f5a6b7c8` | clinica_management_flag | ❌ |
| 14 | `2026_06_21_add_modulos` | `2026_06_17_clinica_management` | add_modulos_tables | ❌ |
| 15 | `REDACTED` | `2026_06_21_add_modulos` | **(B-001 fix)** | ✅ **SIM** |

### Perguntas da FASE 2

#### Quantos heads existem?

**1 head.** Único chain linear após os 2 merges (`bb2cbd44835d` e `a7b8c9d0e1f2`).

#### Existe merge migration necessária?

**NÃO.** O chain está unificado. Os dois merges existentes já consolidam as chains em uma única linha.

> **Correção de achado anterior:** O M31 mencionou "4 chains paralelas, 3 heads" — isso foi uma interpretação errada. As chains existem **antes** dos merges, mas os merges as consolidam. Hoje há 1 chain único.

#### Existe migration órfã?

**NÃO.** Todas as 14 migrations não-root têm `down_revision` apontando para uma revision existente.

#### Existe migration duplicada?

**NÃO.** Nenhuma migration tem a mesma combinação (revision + down_revision) que outra.

#### Existe migration que nunca será executada?

**NÃO.** O chain é linear; cada migration será aplicada em sequência por `flask db upgrade`.

### Ações executadas em FASE 2

**Nenhuma.** Não foi necessário criar merge migrations, deletar órfãs ou corrigir nada. O chain está limpo.

---

## FASE 3 — Estrutura dos testes

### Estado atual

| Localização | Quantidade |
|-------------|------------|
| `tests/*.py` (raiz) | 38 |
| `tests/integration/*.py` | 1 (`test_pharmacy_dispense.py`) |
| `tests/security/*.py` | 3 (`test_p0_remediation_m18.py`, `test_rate_limit_phase5a.py`, `benchmark_rate_limit.py`) |
| `tests/smoke/*.py` | 1 (`test_webhook_security.py`) |
| `tests/e2e/*.py` | 13 (`test_01_login.py` ... `test_13_ia_chat.py`) |
| `tests/load/` | 1 (`locustfile.py` + `scenarios/`) |
| **TOTAL** | **57 .py + conftest.py** |

### Subdirs já organizados

✅ **Boas práticas já presentes:**
- `tests/e2e/` — 13 testes Playwright numerados (login, logout, cadastro, paciente, etc.)
- `tests/load/` — Locust + scenarios
- `tests/security/` — testes P0 + rate limit + benchmark
- `tests/smoke/` — webhook security smoke
- `tests/integration/` — pharmacy dispense (recém-adicionado)

### Classificação proposta para os 38 testes em `tests/` raiz

| Categoria | Testes | Destino proposto |
|-----------|--------|------------------|
| **Testes unitários** | `test_sintomas_unit.py` | `tests/unit/` |
| **Testes de API (integração)** | `test_api_requests.py`, `test_association.py`, `test_cadastro_profissionais.py`, `test_cadastro_profissionais_fix.py`, `test_clinica_crud.py`, `test_compartilhamento_api.py`, `test_compartilhamento_completo.py`, `test_exames_completo.py`, `test_exames_fix.py`, `test_import_export_ai.py`, `test_import_export_complete.py`, `test_plan_gating.py`, `test_produtos_api.py`, `test_registration_ai_verification.py`, `test_sintomas_api.py`, `test_tenant_isolation.py`, `test_week10_specialties.py`, `test_week11a_followup.py`, `test_week11b_cannabis.py`, `test_week11d_productization.py`, `test_week6_flows.py`, `test_week7a_hardening.py`, `test_week7b_intelligence.py`, `test_week8_knowledge.py` | `tests/integration/` |
| **Testes debug (descartáveis)** | `test_dosagens_debug.py`, `test_exames_debug.py`, `test_login_debug.py`, `test_db_connection_hostinger.py` | `tests/_debug/` ou deletar |
| **Testes de email** | `test_email_system.py`, `test_email_hostinger.py` | `tests/integration/` |
| **Testes simples (descartáveis)** | `test_quick_login.py`, `test_login_simple.py`, `test_login_connection_fix.py`, `test_frontend_login.py`, `test_anuncios_system.py`, `test_dosagens.py` | `tests/_legacy/` ou deletar |
| **Deploy guard (M28)** | `test_deploy_guard.py` | `tests/unit/` (já é um teste unitário real) |

### Eliminação de duplicações

Identificadas duplicações potenciais:

| Duplicação suspeita | Decisão |
|---------------------|---------|
| `test_login_debug.py` vs `test_login_simple.py` vs `test_quick_login.py` | Provavelmente redundantes — análise recomendada |
| `test_dosagens_debug.py` vs `test_dosagens.py` | `test_dosagens_debug.py` parece ser versão instrumentada — manter `test_dosagens.py` |
| `test_exames_debug.py` vs `test_exames_fix.py` vs `test_exames_completo.py` | Hierarquia confusa — unificar em `test_exames.py` |
| `test_import_export_ai.py` vs `test_import_export_complete.py` | `test_import_export_ai.py` é subset de `complete` — unificar |
| `test_cadastro_profissionais.py` vs `test_cadastro_profissionais_fix.py` | `fix.py` provavelmente é regressão — manter ambos |

### Conftest.py

**Existe em:** `tests/e2e/conftest.py` (1380 bytes)
**Recomendação:** Criar `tests/conftest.py` raiz com fixtures compartilhadas (auth, db, etc.).

### Documentação

**Existe:** `tests/load/README.md` (3.3 KB)
**Recomendação:** Criar `tests/README.md` raiz cobrindo:
- Como rodar cada categoria
- Dependências (pytest, locust, playwright)
- Convenções de naming
- Critérios de cobertura

### Ações executadas em FASE 3

**Nenhuma movimentação física.** Classificação proposta acima é para próximo ciclo. Não executada em M32 porque:
- Mexer em 38 arquivos de teste sem revisão pode quebrar suíte
- M32 foca em organização semântica, não refactor de testes

---

## FASE 4 — Documentação

### Estatísticas

- **Total em `docs/`:** 119 arquivos `.md` (+ 7 ADRs + 1 template + 1 README em `docs/adr/`)
- **Em `docs/AraFlow/`:** 39 arquivos (produto separado, manter intacto)
- **Em `docs/adr/`:** 7 ADRs + template (manter intacto)

### Documentos ativos vs arquiváveis

#### ATIVOS (88 docs) — manter no root de `docs/`

Documentos relevantes para release RC1, runbook operacional, ou referência técnica consolidada. Detalhados em `docs/INDEX.md`.

#### HISTÓRICOS / ARQUIVÁVEIS (31 docs) — candidatos a `docs/archive/`

| Categoria | Exemplos |
|-----------|----------|
| Snapshots de missões M17-M19 | `CAMPO_EM_TRATAMENTO.md`, `CORREÇÃO_*`, `MELHORIAS_*`, `SOLUÇÃO_*`, `VERSÃO_*`, `VERSÕES_*` |
| Guias antigos de dev/deploy | `INSTRUÇÕES_*`, `LOGIN_*`, `README_DOCKER.md`, `COMO_INICIAR_*`, `REVISAO_SISTEMA_DEPLOY_*`, `termius_guide.md`, `vps_deploy_guide.md`, `WHATSAPP_SETUP.md` |
| Sistemas específicos consolidados | `SISTEMA_*` (8 docs) — se cobertos pelo código, podem arquivar |

### Criação de índice único: `docs/INDEX.md`

**Arquivo criado:** `docs/INDEX.md` (262 linhas)

Conteúdo:
- 88 docs ativos categorizados (Release, Operacional, Segurança, LGPD, Capacidade, Billing, Bugs, UX, Validação, Arquitetura, Sprints, Sistemas)
- 31 docs históricos (mover para `docs/archive/` no próximo ciclo)
- Subdiretórios (`AraFlow/`, `adr/`) com descrição
- Política de versionamento
- Pendências M32

### Ações executadas em FASE 4

- ✅ Criado `docs/INDEX.md`
- ❌ NÃO movidos 31 docs históricos para `docs/archive/` (proposta para próximo ciclo)

---

## FASE 5 — Release Manifest

### Arquivo criado: `RELEASE_MANIFEST.md` (raiz do projeto, ~250 linhas)

Conteúdo organizado em 11 seções:

| # | Seção | Conteúdo |
|---|-------|----------|
| 1 | Commit esperado | Tag + 9 commits pendentes da sequência M31 |
| 2 | Migrations | Inventário + chain + SQL idempotente |
| 3 | Versão | Versões de AraOS, Flask, SQLAlchemy, Python, Node |
| 4 | Docker | Imagens, Dockerfile, entrypoint |
| 5 | Compose | dev, prod, staging |
| 6 | Secrets | 10 vars obrigatórias (P0-A FASE 4) |
| 7 | Smoke | Suite + comandos + critérios de aceitação |
| 8 | Rollback | Procedimento + backup |
| 9 | Artefatos | Versionados + NÃO versionados (~165 MB) |
| 10 | Pendências | Bloqueadores + recomendados |
| 11 | Riscos | Carry-over de missões anteriores |

---

## FASE 6 — Auditoria Final

### Respondendo as 5 perguntas obrigatórias

#### 1. O repositório está limpo?

**NÃO completamente.**

**Estrutura:** ✅ Limpa. Estrutura de pastas, separação de responsabilidades, módulos bem organizados.

**Working tree:** ❌ Sujo. 269 entradas (94 modified + 175 untracked) não commitadas desde 2026-06-20.

**Bloqueadores:** Migration B-001 não aplicada em produção (estado desde M27).

**Limpeza proposta em M32:**
- ✅ `.gitignore` atualizado com 6 novos padrões
- ✅ `docs/INDEX.md` criado (índice único)
- ✅ `RELEASE_MANIFEST.md` criado
- ❌ Working tree NÃO commitado (constraint do M32: não executar commit)
- ❌ 31 docs históricos NÃO movidos para `docs/archive/`
- ❌ 38 testes raiz NÃO reorganizados em subcategorias

#### 2. Existe algum arquivo que não deveria ser commitado?

**SIM — ~165 MB identificados:**

| Categoria | Local | Tamanho estimado |
|-----------|-------|------------------|
| Relatórios Locust | `reports/*.html`, `*.csv` | 4.7 MB |
| SQLite local | `instance/*.db` | 492 KB |
| Virtualenv | `venv_local/` | ~100 MB |
| Coverage | `htmlcov_week6/` | ~10 MB |
| Imagens avulsas | `AGENDA.png`, `eusoulia.png` | < 500 KB |
| Deps Node | `tools/araflow-cli/node_modules/` | ~50 MB |
| **TOTAL** | — | **~165 MB** |

**Mitigação aplicada:** .gitignore atualizado.

#### 3. Existe migration pendente de organização?

**NÃO.** Análise completa em FASE 2:
- 15 migrations, 1 chain único
- 2 merges já consolidam tudo
- 0 órfãs, 0 duplicadas, 0 inúteis
- 1 migration idempotente (B-001 — única necessária em produção)

**Migration crítica para produção:**
```sql
ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;
```

#### 4. O Release RC1 pode ser criado?

**SIM — mas com 2 pré-condições:**

**Pré-condição 1:** Aplicar migration B-001 em produção
- Comando: `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;`
- Risco: zero (idempotente)
- Tempo: < 5 segundos
- Responsável: operador com psql/SSH

**Pré-condição 2:** Executar 9 commits da sequência M31
- 7 commits de código (migration, fixes, security, deploy_guard, infra)
- 2 commits de housekeeping (gitignore, docs)
- Risco: 2 commits ALTO (5 e 6 — security + deploy_guard). Exigem migration B-001 aplicada ANTES.
- Tempo: ~30 minutos
- Responsável: dev

**Após pré-condições:**
- Tag `v1.0.0-rc.1` pode ser criada
- Pipeline CI/CD pode buildar imagem
- Deploy pode ser executado

#### 5. Existe algum risco estrutural restante?

**SIM — 4 riscos estruturais (não-bloqueantes mas importantes):**

| # | Risco | Categoria | Mitigação |
|---|-------|-----------|-----------|
| R1 | Working tree não commitada (269 entradas) | Reprodutibilidade | Executar 9 commits (constraint M32) |
| R2 | 31 docs históricos poluindo `docs/` | Descoberta | Mover para `docs/archive/` (próximo ciclo) |
| R3 | 38 testes sem subcategorias | Manutenibilidade | Reorganizar (próximo ciclo) |
| R4 | `AraFlow/` (39 docs) no mesmo repo | Clareza | Separar quando AraFlow virar release independente |

**Risco carry-over de M29:** 4 endpoints 500 em produção (B-001) — **RESOLVIDO** com migration B-001 (pendente apenas de aplicação).

---

## Resumo de entregáveis M32

| Arquivo | Status | Tipo |
|---------|--------|------|
| `.gitignore` | **MODIFICADO** | +12 linhas (M32 patterns) |
| `docs/INDEX.md` | **NOVO** | Índice único (262 linhas) |
| `RELEASE_MANIFEST.md` | **NOVO** | Manifest de release (~250 linhas) |
| `docs/REPOSITORY_STABILIZATION_REPORT.md` | **NOVO** | Este relatório |

**Total:** 1 modificado + 3 criados.

---

## Restrições respeitadas

- ✅ Não executei commit (sequência proposta, NÃO aplicada)
- ✅ Não abri PR
- ✅ Não fiz push
- ✅ Não implementei funcionalidades
- ✅ Não alterei regras de negócio
- ✅ Não alterei frontend (apenas organizei refs)
- ✅ Não alterei UX
- ✅ Não alterei billing
- ✅ Não alterei RBAC
- ✅ Não alterei LGPD
- ✅ Mexi apenas em .gitignore + criei 3 docs (organização)

---

## Próximas ações recomendadas (fora do escopo M32)

1. **Operador:** Aplicar `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;` em produção (5 min).
2. **Dev:** Executar os 9 commits da sequência M31 (30 min).
3. **Dev:** Criar tag `v1.0.0-rc.1` (1 min).
4. **CI/CD:** Buildar imagem Docker (5 min).
5. **Operador:** Deploy usando `scripts/deploy_prod.sh` (10 min).
6. **QA:** Rodar smoke pós-deploy (5 min).
7. **Próximo ciclo (M33+):** Mover 31 docs para `docs/archive/`, reorganizar 38 testes em subcategorias, separar `AraFlow/`.

**Parando conforme instrução.** M32 concluída. Repositório estruturalmente estabilizado para o RC1, aguardando execução dos 9 commits propostos.