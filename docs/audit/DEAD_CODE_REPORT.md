# DEAD_CODE_REPORT.md — Código Morto, Experimental ou Órfão

**Data:** 2026-07-22
**Escopo:** read-only — inventário de código não-produção sem refactor ou remoção.
**Diretriz:** Apenas catalogação. Sem correções nesta auditoria.

---

## 1. Classificação

| Categoria | Definição | Severidade |
|---|---|:---:|
| **Stub/Experimental** | Criado para prova de conceito, não integrado | 🔴 Alta |
| **Legacy Dead** | Código legado pré-Sprints 4.x sem callers | 🟠 Média |
| **Orphan** | Página ou componente sem rota/usuário | 🟠 Média |
| **Debug** | Tests `test_*_debug.py/_fix.py/_simple.py` em raiz | 🟡 Baixa |
| **Unused Migration** | Migration que não cria nada referenciado | 🟡 Baixa |
| **Duplicado** | Dockerfile/compose/standards | 🟡 Baixa |
| **Documento ausente** | ADR/Norma referenciada mas sem arquivo físico | 🟠 Média |

## 2. Stubs / Experimental (araos/clinical/)

### 2.1 `clinical/graph/` 🔴

- **Conteúdo:** scaffold de "Clinical Graph" — camada relacional
- **Status:** placeholder; nenhum caller
- **Sprint ideia original:** "Clinical Graph — camada relacional" (task #42)
- **Status atual:** task marcada `completed` mas código é stub

### 2.2 `clinical/twin/` 🔴

- **Conteúdo:** scaffold "Digital Twin" stub
- **Status:** existe `models.py` mas sem consumer
- **Nota:** BC Twin REAL está em `routes/twin.py` (legado Flask, 462 linhas funcional)

### 2.3 `clinical/summary/` 🔴

- **Conteúdo:** scaffold "Clinical Summary"
- **engine.py** stub
- **Status:** task #42 Sibling — sem uso

### 2.4 `clinical/projections/` 🔴

- **Conteúdo:** legacy `engine.py`
- **Substituído por:** BCs Sprint 4.x dedicated projections
- **Nenhum import encontrado na grep**

### 2.5 `clinical/profile/` 🟠

- **Conteúdo:** legacy profile-related
- **Status:** chamado apenas por código legado, pode ser substituído por `specialties/cannabis/profile`

## 3. Orfãos Frontend

### 3.1 `NeuroScalesListPage.js` 🟠

- Página existe em `frontend/src/pages/neuro/`
- **Não está registrada em `App.js`** rotas
- Sem entrada de menu
- Sem link em outras páginas

### 3.2 `NeuroScaleApplyPage.js` 🟠

- Similar à anterior — página órfã
- Import `react-router-dom` presente mas rota ausenta

### 3.3 `IntelligentImportPage.js` 🟠

- Apenas **7 linhas** — stub
- Importa `react-router-dom` apenas
- Não funcional

### 3.4 Possíveis páginas órfãs adicionais

Verificação textual em outras páginas seria necessária em sprint dedicada.

## 4. Frontend Auxiliares (32 arquivos)

Apps frontend para casos pontuais:
- `frontend/transcribe/` — transcript helper standalone
- `frontend/simple-frontend/`
- `frontend/accessibility-tester/`
- `frontend/eslint/`
- `frontend/eslint-babel/`
- `frontend/scripts/`
- ... (~25 diretórios auxiliares)

**Status:** desconhecido se em uso ou legados. Arquivos auxiliares podem ser de tests/build.

## 5. Debug / Legacy Tests

### 5.1 Padrões detectados (raiz tests/)

- `test_*_debug.py`
- `test_*_fix.py`
- `test_*_simple.py`
- **39 arquivos totais** nessa categoria (estimativa baseada em naming convention)

Exemplos prováveis:
- `test_auth_debug.py`
- `test_pacientes_fix.py`
- `test_models_simple.py`

> Análise específica de cada arquivo fica como pendência para sprint de housekeeping.

### 5.2 Active Tests (referência)

| Diretório | Funções | Status |
|---|---:|---|
| clinical_event_store/ | 189 | active |
| intel_sprint_4_2/ | 253 | active |
| sprint_4_4_5/ | 176 | active |
| neurodev_sprint_3_2/ | 156 | active |
| neuro_sprint1/ | 128 | active |
| intel_sprint_4_1/ | 117 | active |
| sprint_4_4/ | 94 | active |
| intel_sprint_4_3/ | 88 | active |
| neuro_sprint2/ | 60 | active |
| genome_sprint_4_3_phase_2/conformance | 43 | active |
| security/ | 31 | active |
| raiz (outros) | 332 | mixed |

## 6. Migrations Duplicadas / Mortas

### 6.1 `0331305d2b3c` — dead migration 🟡

- Nome do arquivo: `add_reminder_settings_table.py`
- Conteúdo: modifica tabela `pacientes` (NÃO cria reminder_settings)
- Divergência filename vs conteúdo
- **Recomendação (NÃO executada):** renomear em sprint de housekeeping

### 6.2 Migrations antigas vs 24 catalogadas

- 24 migrations declaradas em `migrations/versions/`
- 2 merge heads resolvidos (G2 entregue)
- Sem migrations duplicadas óbvias (verificação adicional necessária)

## 7. Standards / ADRs Documentados vs Físicos

### 7.1 AraOS Standards Aceitos

| ID | Status | Arquivo físico |
|---|---|---|
| AS-000 | Draft | ✅ existe |
| AS-001 | Published | ✅ existe |
| AS-002 | Draft | ✅ existe |
| AS-003 | Pós-implementação | ✅ existe |
| AS-004 | Draft 0.1 (Sprint 4.4.5) | ✅ existe |
| AS-005 | (proposto) | 🔴 não existe |
| AS-006 | (proposto) | 🔴 não existe |

### 7.2 ADRs AraOS

| ID | Status | Arquivo físico |
|---|---|---|
| ADR-0001 | Accepted | ✅ |
| ADR-0002 | Accepted | ✅ |
| ADR-0003 | Proposed | ✅ |
| ADR-0004 | Histórico (superseded) | ✅ |
| ADR-0005 | Accepted | ✅ |
| ADR-0006 | Acceptable | ✅ |
| ADR-0007 | **Não existe (gap)** | 🔴 |
| ADR-0008 | Proposed | ✅ |

### 7.3 ADRs AraFlow

**Status:** README declara 15 ADRs como Accepted (001-015) mas **apenas 14 arquivos físicos** (016-029).

| Faixa | Status | Físicos |
|---|---|---|
| 001-015 | referenciados | 🔴 0 arquivos |
| 016-029 | implementados | ✅ 14 arquivos |

**Gap:** os 15 ADRs referenciados no README como Accepted **não têm arquivos físicos**. Pode ser numeração alternativa.

## 8. Dockerfiles Duplicados

- 9 Dockerfiles no repositório
- `Dockerfile.dockerfile` (nome enigmático)
- `Dockerfile.js` (idem)
- Ambos **aparentemente idênticos** (verificação adicional necessária)

## 9. Services Legacy em `services/`

77 arquivos. Maioria ativos, alguns candidatos a:
- `services/legacy_*.py`
- `services/migrations.py` (script manual — substituído por Alembic)
- `services/backup_old.py`

**Verificação específica** de cada serviço fica para sprint de housekeeping.

## 10. Routes com Tamanho Suspeito (potencialmente duplicados)

| Rota | Linhas | Status |
|---|---:|---|
| ai_management.py | 1262 | ativo |
| pacientes.py | 910 | ativo |
| ai_config.py | 541 | ativo |
| intelligent_import.py | 573 | ativo |
| ai_clinical.py | 119 | ativo |

Análise de duplicação interna fica para sprint dedicada.

## 11. Cobertura de Código Morto Estimada

| Tipo | Estimativa Linhas Mortas |
|---|---:|
| Stubs `clinical/graph` + `twin` + `summary` + `projections` | ~500 |
| Páginas órfãs (2 neuro + 1 stub) | ~500 |
| 39 tests debug/fix | ~2.000 |
| AraFlow ADRs 001-015 (físicos) | 0 (não há) |
| Dockerfiles duplicados | ~50 |
| Migration dead + 24 arquivos | ~100 |
| ~10 services legacy | ~1.500 |
| **Total estimado morto/órfão** | **~4.500-5.000 linhas** |

Em um repositório de ~150.000 linhas totais, **~3%** é código morto/órfão (estimativa).

## 12. Recomendações de Catalogação (não-execução)

> **Não executar nesta sprint** (regra: read-only audit).

Sprint dedicada de housekeeping deve:
1. Identificar cada arquivo `_debug/_fix/_simple.py` e remover
2. Remover `clinical/graph`, `clinical/twin` (stubs), `clinical/projections`, `clinical/summary`
3. Remover páginas órfãs Neuro + IntelligentImportPage
4. Renomear migration 0331305d2b3c para refletir conteúdo real
5. Decidir destino dos AraFlow ADRs 001-015 (recriar arquivos ou atualizar README)
6. Remover Dockerfiles duplicados
7. Migrar scripts `services/migrations.py` para Alembic (já feito parcialmente)

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [BACKEND_AUDIT.md](BACKEND_AUDIT.md)
