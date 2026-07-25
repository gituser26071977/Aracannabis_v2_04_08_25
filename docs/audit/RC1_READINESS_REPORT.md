# RC1_READINESS_REPORT.md — Avaliação de Prontidão para Release Candidate 1

**Data:** 2026-07-22
**Diretriz:** DIRETRIZ PÓS-AUDITORIA — ARAOS RC1
**Escopo:** avaliação objetiva, sem início de nova sprint clínica, sem novas funcionalidades.

---

## 1. Resposta Objetiva

> **Veredicto:** 🟡 **RC1 ainda NÃO pronto.**
>
> Faltam 4 entregas CORE + 1 integração + 1 validação E2E para que o pipeline técnico do Knowledge Engine esteja completo, persistente e demonstrável sem mocks/InMemory.
>
> Esforço total estimado: **2-3 sprints de 1 semana cada** (reuso máximo de código existente).

---

## 2. Classificação das Pendências por Categoria

### 2.1 CORE (sem isto o Knowledge Engine não funciona)

| # | Pendência | Status Atual | Esforço Estimado | Bloqueio E2E? |
|---|---|---|---:|:---:|
| C1 | W1.3 SQLKnowledgeRepository | Mappers prontos (585 linhas em `infrastructure/mappers.py`); classe SQL não existe | 1 sprint | Sim |
| C2 | W1.5 KnowledgeUnitOfWork | Não existe | 0.5 sprint | Sim |
| C3 | W1.7 PostgreSQL Integration Tests | Diretório `tests/sprint_4_5/` não existe | 0.5 sprint | Sim |
| C4 | Task #197 hypothesis_id cross-tenant fix | Não iniciada | 0.2 sprint | Sim (manifest/code gap) |
| C5 | Migration REDACTED já executada em dev? | Criada mas nunca rodada em PostgreSQL real | 0.1 sprint (verify) | Sim |

### 2.2 INTEGRAÇÃO (conecta componentes existentes)

| # | Pendência | Status Atual | Esforço Estimado | Bloqueio E2E? |
|---|---|---|---:|:---:|
| I1 | Wave 3 REST `/api/knowledge/*` (14 endpoints) | 0 implementados | 1 sprint | Sim |
| I2 | Wave 4 Dashboard (React) | 0 implementação encontrada; reuso possível com `IntelligenceTimelinePage` + `ExplainabilityPage` | 1 sprint | Sim |
| I3 | E2E Flow validation | Nunca executado | 0.5 sprint | Sim |

### 2.3 HARDENING (segurança/robustez — PÓS-RC1)

| Item | Status | Decisão RC1 |
|---|---|---|
| RBAC completo (106 perms) | 0 endpoints aplicam | **DEFERRED para Production Hardening** |
| Tenant unificado | 3 mecanismos divergentes | DEFERRED |
| Audit Ledger AraOS central | Código pronto, sem integração | DEFERRED |
| Refresh Token Flask | Não emitido | DEFERRED |
| CSRF cross-cutting | Helper existe, 0 aplicação | DEFERRED |
| MFA operacional | Modelo, sem OTP | DEFERRED |

### 2.4 HOUSEKEEPING (baixa prioridade)

| Item | Status | Decisão RC1 |
|---|---|---|
| Stubs clinical/{graph,twin,summary,projections} | Existentes sem caller | Removíveis após RC1 |
| Páginas órfãs (NeuroScalesList, NeuroScaleApply, IntelligentImport) | Sem rota | Removíveis |
| 39 tests `_debug/_fix/_simple.py` | Provavelmente legados | Auditoria específica depois |
| Migration 0331305d2b3c dead | Nome divergente | Rename depois |
| Dockerfiles duplicados | Encontrados | Remover depois |
| AraFlow ADRs 001-015 sem arquivos | Gap documental | Reconciliar depois |

---

## 3. Componentes Já Reutilizáveis (sem código novo)

### 3.1 Backend (já existentes, prontos para integrar)

| Componente | Arquivo | Reuso |
|---|---|---|
| `KnowledgeService.run_pipeline` | `araos/clinical/knowledge/application/knowledge_service.py` | Total — orquestra todos os sub-services |
| `InMemoryKnowledgeRepository` | `araos/clinical/knowledge/infrastructure/in_memory.py` | Substituível por SQL; ABC já preparado |
| `KnowledgeRepository` ABC tenant-bound | `araos/clinical/knowledge/infrastructure/repository.py` | G3 entregue — reuso direto |
| `KnowledgeService.build_genome_from_events` | mesmo | Reuso |
| `CorrelationService.execute_all` | `araos/clinical/knowledge/application/correlation_service.py` | Reuso |
| `HypothesisService.generate` | `hypothesis_service.py` | Reuso |
| `GraphService.build` | `graph_service.py` | Reuso |
| `CohortService.execute` | `cohort_service.py` | Reuso |
| `ResearchService.execute + replay` | `research_service.py` | Reuso |
| `SqlAlchemyClinicalEventStore` | `araos/clinical/event_store/store.py` | Reuso; parâmetro `autocommit` adicionado em W1.6 |
| `ClinicalGene` AR | `araos/clinical/genome/domain/clinical_gene.py` | Reuso |
| `ClinicalGenome` AR | `araos/clinical/knowledge/domain/clinical_genome.py` | Reuso |
| `Explanation` VO | `araos/clinical/explainability/` | Reuso |
| `TimelineQuery` | `araos/clinical/timeline/application/query.py` | Reuso |
| `KnowledgeComposition` | `application/composition.py` (proposta W2.1) | **Criar — não existe** |

### 3.2 Frontend (já existentes, prontos para conectar)

| Página | Arquivo | Pode ser reaproveitada |
|---|---|---|
| `IntelligenceTimelinePage.js` | `frontend/src/pages/` | **Sim** — adicionar filtros Knowledge |
| `ExplainabilityPage.js` | `frontend/src/pages/` | **Sim** — conectar a Explanation API |
| `ClinicalContextPage.js` | `frontend/src/pages/` | Adjacente — opcional |
| `AIDashboardPage.js` | `frontend/src/pages/` | **Sim** — pode hospedar Knowledge metrics |
| `AIAssistantPage.js` | `frontend/src/pages/` | **Sim** — pode conectar Knowledge queries |
| `PharmacistDashboard.js` | `frontend/src/pages/` | Não aplicável |
| `DashboardPage.js` | `frontend/src/pages/` | **Sim** — adicionar widget Knowledge |

### 3.3 Componentes React (reutilizáveis)

| Componente | Onde | Reuso |
|---|---|---|
| `TimelineEntry.js` | `components/` | Total — exibir Knowledge events |
| `ExplanationPanel.js` | `components/` | Total — exibir Explanation API |
| `TwinVisualizer.js`, `TwinGraph.js` | `components/` | Adaptar para KnowledgeGraph |
| `DataTable.js`, `FilterBar.js`, `Pagination.js` | `components/` | Total — tabelas de genes/cohorts |
| `ConfirmDialog.js`, `Toast.js`, `EmptyState.js` | `components/` | Total — UX básico |
| `Wizard.js` | `components/` | Adaptar para pipeline run |

### 3.4 Endpoints REST (já existentes, complementares)

| Endpoint | Função | Reuso |
|---|---|---|
| `/api/timeline/*` | Sprint 4.1 | **Sim** — consumido pelo Knowledge |
| `/api/explainability/*` | Sprint 4.1 | **Sim** — consumido pelo Knowledge |
| `/api/intelligence/*` | Legacy | **Sim** — agrupador natural |
| `/api/clinical/contexts/*` | Sprint 4.2 | Adjacente — consumir contexto como evidência |

---

## 4. Componentes Novos Necessários (mínimo absoluto)

| Componente | Razão | Esforço |
|---|---|---:|
| `SQLKnowledgeRepository` (W1.3) | Persistência obrigatória | incluso em C1 |
| `KnowledgeUnitOfWork` (W1.5) | Transação atômica | incluso em C2 |
| `KnowledgeComposition` (W2.1) | Composição service+repo | 0.2 sprint |
| `@tenant_required` decorator (W3.1) | Isolamento básico | 0.2 sprint |
| `interfaces/rest/genome.py`, etc. (W3.2) | Exposição REST | incluso em I1 |
| `interfaces/rest/dto.py` (W3.3) | DTOs de resposta | incluso em I1 |
| `interfaces/rest/audit.py` (W3.6) | Audit mínimo | 0.2 sprint |
| `KnowledgeGraphViewer.js`, `CohortDashboard.js`, `ResearchReplay.js`, `ExplainabilityDashboard.js`, `CorrelationExplorer.js` (W4.1) | Visualização | incluso em I2 |
| `frontend/src/services/knowledgeApi.js` (W4.2) | HTTP client Knowledge | incluso em I2 |

**Total estimado:** ~3 sprints com reuso máximo.

---

## 5. Fluxo End-to-End Validado (target RC1)

### 5.1 Sequência esperada

```
1. Cadastro de paciente (SIAP legado / frontend já existente)
   ↓
2. Registro de eventos clínicos (Clinical Event Store já funcional)
   ↓
3. Replay (ReplayEngine já funcional)
   ↓
4. Geração do Clinical Genome (KnowledgeService.build_genome_from_events)
   ↓
5. Geração do Knowledge Graph (GraphService.build)
   ↓
6. Correlations (CorrelationService.execute_all)
   ↓
7. Hypotheses (HypothesisService.generate)
   ↓
8. Explainability (ExplanationRegistry.get)
   ↓
9. Persistência PostgreSQL (SQLKnowledgeRepository via KnowledgeUnitOfWork)
   ↓
10. Consulta via REST (/api/knowledge/genomes, /api/knowledge/correlations, etc.)
   ↓
11. Visualização no Dashboard React (KnowledgeGraphViewer + ExplainabilityDashboard)
```

### 5.2 Estado atual

| Etapa | Estado | Evidência |
|---|---|---|
| 1. Cadastro de paciente | 🟢 OK | `routes/pacientes.py` + frontend |
| 2. Registro de eventos | 🟢 OK | `clinical_event_store` |
| 3. Replay | 🟢 OK | `genome/app/replay_engine.py` |
| 4. Clinical Genome | 🟢 OK | `knowledge_service.build_genome_from_events` (InMemory) |
| 5. Knowledge Graph | 🟢 OK | `graph_service.build` (InMemory) |
| 6. Correlations | 🟢 OK | `correlation_service.execute_all` (InMemory) |
| 7. Hypotheses | 🟢 OK | `hypothesis_service.generate` (InMemory) |
| 8. Explainability | 🟢 OK | `explanation_registry.get` (InMemory) |
| **9. Persistência PostgreSQL** | **🔴 FALTA** | SQLKnowledgeRepository não existe |
| **10. Consulta via REST** | **🔴 FALTA** | 0 endpoints `/api/knowledge/*` |
| **11. Dashboard React** | **🔴 FALTA** | 0 páginas Knowledge |

**8 de 11 etapas OK com InMemory.** 3 etapas com persistência real pendentes.

---

## 6. Restrições e Regras para RC1

### 6.1 Não modificar

- `araos/clinical/knowledge/domain/*` (FROZEN, Architecture Freeze)
- `araos/clinical/genome/domain/*` (FROZEN)
- `araos/clinical/event_store/domain/*` (FROZEN)
- `araos/clinical/timeline/domain/*` (FROZEN)
- `araos/clinical/context/domain/*` (FROZEN)
- `araos/clinical/explainability/domain/*` (FROZEN)
- AS-000/001/002, ASM-001 (Foundation Freeze)
- ADR-0001..0006 (Foundation Freeze)

### 6.2 Permitido (infraestrutura e integração)

- Adicionar `infrastructure/sql.py`, `infrastructure/unit_of_work.py`
- Adicionar `interfaces/rest/`
- Adicionar `@tenant_required` decorator (mínimo)
- Adicionar `frontend/src/pages/knowledge/*`
- Adicionar `frontend/src/services/knowledgeApi.js`

### 6.3 Não criar

- Novos bounded contexts
- Novos application services no Knowledge
- Novos Domain Events
- Novos ARs ou VOs
- Modificações em `models.py` legado
- Refactor de endpoints legados

---

## 7. Pendências para Production Hardening (pós-RC1)

| Item | Status | Prio. |
|---|---|:---:|
| @require_permission cross-cutting em 57 blueprints | pendente | 🔴 |
| Tenant unificado (1 mecanismo) | pendente | 🔴 |
| Audit Ledger AraOS conectado a rotas | pendente | 🟠 |
| Refresh Token Flask integrado | pendente | 🟠 |
| CSRF cross-cutting decorator | pendente | 🟠 |
| MFA TOTP | pendente | 🟠 |
| SECRET_KEY -> env var | pendente | 🟠 |
| ADR-0007 (V1/V2 + hypothesis_id) | pendente | 🟠 |
| JWT revocation Redis | pendente | 🟡 |
| Frontend tests baseline | pendente | 🟡 |
| Coverage PostgreSQL gate | pendente | 🟡 |

---

## 8. Estimativa Consolidada

### 8.1 FASE 1 — Finalizar Sprint 4.5 (CORE)

| Tarefa | CORE | Esforço |
|---|:---:|---:|
| W1.3 SQLKnowledgeRepository (sql.py) | C1 | 1.0 sprint |
| W1.5 KnowledgeUnitOfWork | C2 | 0.5 sprint |
| W1.7 PostgreSQL Integration Tests | C3 | 0.5 sprint |
| Task #197 hypothesis_id fix | C4 | 0.2 sprint |
| Migration verify + run real | C5 | 0.1 sprint |
| **Subtotal Fase 1** | | **~2.3 sprints** |

### 8.2 FASE 2 — Knowledge API (INTEGRAÇÃO)

| Tarefa | INTEGRAÇÃO | Esforço |
|---|:---:|---:|
| @tenant_required decorator mínimo | I1a | 0.2 sprint |
| `interfaces/rest/*` (14 endpoints) | I1b | 0.6 sprint |
| `interfaces/rest/dto.py` | I1c | 0.1 sprint |
| KnowledgeComposition | I1d | 0.2 sprint |
| Audit mínimo por endpoint | I1e | 0.2 sprint |
| Testes REST | I1f | 0.3 sprint |
| **Subtotal Fase 2** | | **~1.6 sprints** |

### 8.3 FASE 3 — Dashboard (INTEGRAÇÃO)

| Tarefa | INTEGRAÇÃO | Esforço |
|---|:---:|---:|
| `frontend/src/services/knowledgeApi.js` | I2a | 0.1 sprint |
| KnowledgeGraphViewer (reuso TwinGraph) | I2b | 0.3 sprint |
| CohortDashboard (reuso DataTable) | I2c | 0.2 sprint |
| ResearchReplay (reuso Wizard) | I2d | 0.2 sprint |
| ExplainabilityDashboard (reuso ExplanationPanel) | I2e | 0.2 sprint |
| CorrelationExplorer | I2f | 0.2 sprint |
| Integração AuthContext | I2g | 0.1 sprint |
| **Subtotal Fase 3** | | **~1.3 sprints** |

### 8.4 FASE 4 — E2E Flow (VALIDAÇÃO)

| Tarefa | Validação | Esforço |
|---|:---:|---:|
| Script de demo E2E | I3a | 0.2 sprint |
| Shadow Compare InMemory vs SQL | I3b | 0.2 sprint |
| Demo UI flow | I3c | 0.2 sprint |
| Registro de inconsistências | I3d | 0.1 sprint |
| **Subtotal Fase 4** | | **~0.7 sprints** |

### 8.5 Total RC1

| Fase | Categoria | Esforço |
|---|---|---:|
| Fase 1 | CORE | ~2.3 sprints |
| Fase 2 | INTEGRAÇÃO | ~1.6 sprints |
| Fase 3 | INTEGRAÇÃO | ~1.3 sprints |
| Fase 4 | VALIDAÇÃO | ~0.7 sprints |
| **TOTAL** | | **~5.9 sprints ≈ 6 sprints** |

---

## 9. Recomendação

### 9.1 Para o RC1 estar pronto

Executar as 4 fases em sequência (CORE primeiro porque INTEGRAÇÃO depende de CORE).

### 9.2 Pós-RC1 — Production Hardening

Após RC1 aceito, executar a fase Hardening com:
- RBAC cross-cutting
- Tenant unificado
- Audit Ledger
- Refresh Token
- CSRF
- MFA

### 9.3 Pós-Hardening — Housekeeping

Limpeza de código morto, ADRs históricos, migration renames, etc.

---

## 10. Decisão Recomendada

> **🟡 RC1 ainda NÃO pronto.**
>
> Iniciar **Fase 1 imediatamente** (Sprint 4.5 W1.3 + W1.5 + W1.7 + task #197).
>
> Após Fase 1 aceita, proceder Fases 2-4 sequencialmente.
>
> Em paralelo, criar ADR-0007 (V1/V2 + hypothesis_id) e ADR-0009 (Production Hardening scope).

### Próximas ações Imediatas

1. ✅ Aprovar este relatório
2. Iniciar Fase 1.1 — SQLKnowledgeRepository (sql.py)
3. Após mappers.py (já existe), escrever sql.py usando mappers
4. Após sql.py, escrever unit_of_work.py
5. Após UoW, escrever testes PostgreSQL integração
6. Em paralelo, fix hypothesis_id (task #197) + ADR-0007

---

**Ver também:**
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- [MVP_GAP_ANALYSIS.md](MVP_GAP_ANALYSIS.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
