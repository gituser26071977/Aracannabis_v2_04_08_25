# RC1_ENGINEERING_REVIEW.md — Revisão Arquitetural Pré-Implementação

**Data:** 2026-07-22
**Diretriz:** DIRETRIZ RC1 — ENGINEERING REVIEW ANTES DA IMPLEMENTAÇÃO
**Papel:** Staff Engineer responsável pela arquitetura
**Escopo:** revisão técnica read-only. Nenhuma alteração de código nesta fase.
**Mandato:** "A melhor implementação é aquela que entrega o RC1 escrevendo a menor quantidade possível de código novo."

---

## 1. Executive Summary

> **🟢 Plano revisado com otimizações.**
>
> O plano aprovado está sólido mas superdimensionado em 3 dimensões:
> - 14 endpoints REST → **6 endpoints** (reutilizar `/api/intelligence/*`)
> - 5 páginas Dashboard → **1 página** (estender `AIDashboard.js`)
> - KnowledgeUnitOfWork próprio → **desnecessário** (SQLAlchemy Session + composição já é UoW)
>
> Não há necessidade de reestruturar — apenas cortar.
>
> Estimativa revisada: **~3.5 sprints** (vs 5.9 original). **~40% redução de código novo**.

### 1.1 Achados Críticos (3 cortes)

| # | Corte | Justificativa | Economia |
|---|---|---|---:|
| 1 | Remover criação de `KnowledgeUnitOfWork` classe | Session SQLAlchemy + `with session_factory() as session:` já é UoW. `autocommit=False` já adicionado em W1.6. Não há precedente de UoW no AraOS. | ~300 linhas |
| 2 | Cortar 8 endpoints REST redundantes | `/api/intelligence/timeline`, `/api/intelligence/explanations`, `/api/intelligence/contexts` JÁ EXISTEM com mesma semântica. `KnowledgePipelineResult` DTO JÁ embute genome+correlations+hypotheses+graph. | ~400 linhas |
| 3 | Cortar 4 páginas Dashboard | Componentes genéricos `PageHeader`/`EmptyState`/`LoadingState`/`DataTable` inline + 1 página `KnowledgeDashboardPage` com tabs cobre todo o caso. Sem biblioteca de grafo disponível — usar lista com chips. | ~600 linhas |

### 1.2 Achados Menores (consolidação)

- E2E 11 passos → **5 passos** (colapsar pipeline em 1 chamada `POST /pipelines/run`)
- Tech Debt classificado: 7 críticos → apenas 1 obrigatório (hypothesis_id); resto Production Hardening
- 4 páginas órfãs / stubs já identificados — não impedir RC1

---

## 2. Oportunidades de Reutilização por Componente

### 2.1 SQLKnowledgeRepository — **70% reuso já existente**

**Já pronto e reusável:**

| Ativo | Local | Tamanho | Estado |
|---|---|---:|---|
| `KnowledgeRepository` ABC tenant-bound | `araos/clinical/knowledge/infrastructure/repository.py` | 341 linhas | ✅ pronto (G3) |
| `InMemoryKnowledgeRepository` | `araos/clinical/knowledge/infrastructure/in_memory.py` | 360 linhas | ✅ pronto, mas precisa `tenant_id` no constructor |
| Mappers lossless | `araos/clinical/knowledge/infrastructure/mappers.py` | 586 linhas | ✅ pronto |
| Migration Alembic | `migrations/versions/REDACTED.py` | — | ✅ criada |
| `Base` + `AuditFieldsMixin` + `Mapped[...]` | `araos/platform/tenant/models.py` | — | ✅ padrão estabelecido |
| `SqlAlchemyClinicalEventStore` com `autocommit=False` | `araos/clinical/event_store/store.py` | 280 linhas | ✅ W1.6 entregue |
| Composite PK pattern `(tenant_id, ...)` | Sprint 4.5 migration | — | ✅ G3 estabelecido |
| Tenant filtering via `tenant_lib.py` `do_orm_execute` | `tenant_lib.py` | — | ✅ Flask-side (não aplicável ao araos) |

**Templates SQL a seguir (já validados):**

| Classe | Padrão | Linhas | Onde |
|---|---|---:|---|
| `REDACTED` | session_factory + session-per-method + commit-on-method | 159 | `araos/clinical/context/sql.py:447-606` |
| `SqlAlchemyClinicalContextQuery` | session_factory + read-only sem commit | 152 | `araos/clinical/context/sql.py:287-439` |
| `REDACTED` | idem, 7 métodos CRUD | 79 | `araos/clinical/context/sql.py:614-693` |
| `SqlAlchemyExplanationRegistry` | session_factory + register/get/list | 90 | `araos/clinical/explainability/sql.py:204-294` |
| `SqlAlchemyClinicalRepository` (legacy) | db_session + commit-on-method | 75 | `araos/clinical/repository.py:63-138` |

**Estimativa de reuso: 70% (template + ABC + mappers + padrão).**

**O que precisa ser criado (sql.py):**

| Item | Linhas estimadas | Razão |
|---|---:|---|
| 7 modelos SQLAlchemy 2.0 (herdando `Base, AuditFieldsMixin`) | ~150 | Necessário para session bind |
| Classe `SQLKnowledgeRepository(KnowledgeRepository)` | ~300 | Implementa 21 métodos abstratos |
| Module-level `session_factory: Callable[[], Session]` type hint | ~5 | — |
| `_row_to_X / _X_to_row` helpers | ~150 | Simetria com mappers.py (lossless via JSON) |
| **Total** | **~605 linhas** | — |

**Percentual real de reuso:** dos arquivos NOVOS, ~70% é repetição de padrão validado. ~30% é lógica específica do Knowledge.

### 2.2 KnowledgeUnitOfWork — **NÃO CRIAR**

> **Veredicto:** Não criar classe `KnowledgeUnitOfWork`. Reutilizar `session_factory` como "UnitOfWork implícito".

**Análise:**

| Argumento | Decisão |
|---|---|
| "UoW coordena múltiplos repositórios" | ✅ verdadeiro |
| "Existe precedente de UoW no AraOS?" | ❌ **ZERO precedentes**. Grep confirmou: nenhuma classe `*UnitOfWork`, `*Transaction`, `*SessionScope`, nem `with session.begin():` em `araos/` |
| "Session SQLAlchemy já é UoW?" | ✅ **SIM**, semanticamente. `session.commit()`/`session.rollback()` no `__exit__` é exatamente o padrão UoW do Fowler |
| "Composições similares já funcionam?" | ✅ `SqlAlchemyClinicalEventStore` com `autocommit=False` + `flush()` + commit externo é o padrão. Neurodev `RegistryProjection.apply_batch` faz exatamente isso |
| "Criar classe custaria quanto?" | ~150 linhas para gestão de erros, lifecycle, etc. |
| "Quanto reuso entrega?" | Zero — não há nada para reusar |

**Recomendação:** Substituir `KnowledgeUnitOfWork` por uma `KnowledgeComposition` que é simplesmente um context manager:

```python
@contextmanager
def knowledge_composition(session_factory, tenant_id):
    session = session_factory()
    try:
        repo = SQLKnowledgeRepository(session, tenant_id)
        event_store = SqlAlchemyClinicalEventStore(session, autocommit=False)
        yield KnowledgeComposition(repo=repo, event_store=event_store, session=session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Esta composição:
- Reusa `session_factory` (parâmetro de injeção)
- Reusa `SqlAlchemyClinicalEventStore` (já com `autocommit=False`)
- Reusa `SQLKnowledgeRepository` (a ser criado)
- É o padrão exato de Neurodev Registry Projection
- Custo: ~30 linhas em `application/composition.py`

### 2.3 REST Layer — **14 → 6 endpoints (-57%)**

**Endpoints propostos no plano original (14):**

| # | Endpoint Proposto | Permissão | Status pós-review |
|---:|---|---|:---:|
| 1 | `GET /api/knowledge/genomes` | `INTELLIGENCE_CORRELATION_READ` | ✅ MANTER |
| 2 | `GET /api/knowledge/genomes/<id>` | `INTELLIGENCE_CORRELATION_READ` | ✅ MANTER (com correlações/hypotheses/graph inline) |
| 3 | `GET /api/knowledge/correlations` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — filtrar via `/genomes/<id>` |
| 4 | `GET /api/knowledge/correlations/<id>` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — embutido em `/genomes/<id>` |
| 5 | `POST /api/knowledge/correlations/compute` | `INTELLIGENCE_CORRELATION_COMPUTE` | 🔴 **REMOVER** — unificar em `/pipelines/run` |
| 6 | `GET /api/knowledge/hypotheses` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — embutido em `/genomes/<id>` |
| 7 | `GET /api/knowledge/hypotheses/<id>` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — embutido em `/genomes/<id>` |
| 8 | `GET /api/knowledge/cohorts` | `INTELLIGENCE_COHORT_READ` | ✅ MANTER |
| 9 | `GET /api/knowledge/cohorts/<id>` | `INTELLIGENCE_COHORT_READ` | ✅ MANTER |
| 10 | `POST /api/knowledge/cohorts` | `INTELLIGENCE_COHORT_DEFINE` | ✅ MANTER |
| 11 | `GET /api/knowledge/graphs` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — embutido em `/genomes/<id>` |
| 12 | `GET /api/knowledge/graphs/<id>` | `INTELLIGENCE_CORRELATION_READ` | 🔴 **REMOVER** — embutido em `/genomes/<id>` |
| 13 | `GET /api/knowledge/research/sessions` | `INTELLIGENCE_ANALYTICS_READ` | 🔴 **REMOVER** — sessões internas |
| 14 | `GET /api/knowledge/research/sessions/<id>` | `INTELLIGENCE_ANALYTICS_READ` | ✅ MANTER (replay) |

**Endpoints ADICIONAIS (já cobertos):**

| Endpoint | Já existe em | Decisão |
|---|---|:---:|
| `POST /api/knowledge/replay` | `/api/intelligence/contexts/<id>/reopen` (análogo) | 🔴 **REMOVER** — usar `/pipelines/run` novamente |
| `GET /api/knowledge/explanations/<id>` | `/api/intelligence/explanations/<id>` | 🔴 **REMOVER** — **DUPLICAÇÃO DIRETA** |
| `GET /api/knowledge/events` | `/api/intelligence/timeline/<patient_id>` | 🔴 **REMOVER** — **DUPLICAÇÃO DIRETA** |
| `POST /api/knowledge/research/execute` | — | 🔴 **REMOVER** — unificar em `/pipelines/run` |

**API final revisada (6 endpoints):**

| # | Método | Rota | Permissão | Reuso |
|---:|---|---|---|---|
| 1 | POST | `/api/knowledge/pipelines/run` | `INTELLIGENCE_CORRELATION_COMPUTE` | KnowledgeService.run_pipeline |
| 2 | GET | `/api/knowledge/genomes` | `INTELLIGENCE_CORRELATION_READ` | KnowledgeRepository.list_genomes |
| 3 | GET | `/api/knowledge/genomes/<genome_id>` | `INTELLIGENCE_CORRELATION_READ` | load_genome + inline correlations/hypotheses/graph (via DTO) |
| 4 | GET | `/api/knowledge/cohorts` | `INTELLIGENCE_COHORT_READ` | KnowledgeRepository.list_cohorts |
| 5 | GET | `/api/knowledge/cohorts/<cohort_id>` | `INTELLIGENCE_COHORT_READ` | load_cohort |
| 6 | POST | `/api/knowledge/cohorts` | `INTELLIGENCE_COHORT_DEFINE` | save_cohort |
| 7 | GET | `/api/knowledge/research/sessions/<session_id>` | `INTELLIGENCE_ANALYTICS_READ` | load_session (replay) |

**Redução:** 14+4 → **7 endpoints** (-57%). Cobertura 100% via `/api/intelligence/*` para os itens removidos.

**Justificativa técnica:** o `KnowledgePipelineResult` DTO **já embute** `genome + correlations + hypotheses + graph`. Separar em endpoints distintos é overhead de cliente sem benefício. Cliente que precisa de um hypothesis específico carrega o genome e filtra in-memory.

### 2.4 Dashboard — **5 páginas → 1 página (-80%)**

**Páginas propostas no plano original (5):**

| Página | Justificativa para remover |
|---|---|
| `KnowledgeGraphViewer.js` | 🔴 sem biblioteca de grafo (recharts é só chart, não network); inline na página principal |
| `CohortDashboard.js` | 🔴 uma tab dentro de `KnowledgeDashboardPage` |
| `ResearchReplay.js` | 🔴 uma tab dentro de `KnowledgeDashboardPage` |
| `ExplainabilityDashboard.js` | 🔴 `/api/intelligence/explanations/<id>` já existe; **NÃO DUPLICAR** |
| `CorrelationExplorer.js` | 🔴 embutido em `/genomes/<id>` (já retorna correlações inline) |

**Página única proposta:** `KnowledgeDashboardPage.js` em `frontend/src/pages/knowledge/`.

**Estrutura (composição):**

```
KnowledgeDashboardPage
├── PageHeader (existente)
├── Tabs (MUI Tabs)
│   ├── Tab 0: Genomes (lista + detail panel)
│   ├── Tab 1: Cohorts (lista + create form)
│   ├── Tab 2: Pipelines (run + history)
│   └── Tab 3: Research Sessions (replay)
└── ErrorBoundary (existente)
```

**Componentes reusados (todos já existentes):**

| Componente | Já existe em |
|---|---|
| `PageHeader` | `components/PageHeader.js` |
| `EmptyState` | `components/EmptyState.js` |
| `LoadingState` | `components/LoadingState.js` |
| `ContextualTip` | `components/ContextualTip.js` |
| `ErrorBoundary` | `components/ErrorBoundary.js` |
| `GlassCard` | `components/ui/GlassCard.js` |
| `useConfirm` | `hooks/useConfirm.js` |
| `useNotifier` | `hooks/useNotifier.js` |

**Padrão estrutural a seguir:** `neuro/NeuroScalesListPage.js` (cards grid + filtros + EmptyState + LoadingState).

**Não criar:**
- `TimelineEntry.js` — extrair inline se necessário, mas para RC1 não é necessário
- `ExplanationPanel.js` — não duplicar Explainability (Sprint 4.1 já tem UI)
- `TwinGraph.js` / `TwinVisualizer.js` — sem lib de grafo disponível; usar lista com chips
- `DataTable.js` — usar MUI Table direto
- `FilterBar.js` — usar TextField inline
- `Wizard.js` — não necessário para RC1

**API service:** criar `frontend/src/services/knowledgeApi.js` seguindo o padrão de `neuroService.js` (já existe).

### 2.5 End-to-End — **11 passos → 5 passos (-55%)**

**Sequência original (11 passos):**

```
1. Cadastro de paciente
2. Registro de eventos
3. Replay
4. Geração do Clinical Genome
5. Geração do Knowledge Graph
6. Correlations
7. Hypotheses
8. Explainability
9. Persistência PostgreSQL
10. Consulta via REST
11. Visualização no Dashboard
```

**Sequência revisada (5 passos):**

```
1. Cadastro de paciente (já funciona — SIAP legado)
2. POST /api/knowledge/pipelines/run {patient_id, window}
   └─ Executa: events → replay → genome → graph → correlations → hypotheses
   └─ Persiste tudo em PostgreSQL (via UoW implícito = context manager)
3. GET /api/knowledge/genomes/<genome_id>
   └─ Retorna genome com correlações, hypotheses, graph inline (via DTO)
4. GET /api/knowledge/research/sessions/<session_id> (opcional — replay)
5. GET no frontend (KnowledgeDashboardPage Tab 0/1/2)
```

**Etapas eliminadas por design:**
- Etapas 2-8 do plano original → colapsadas em 1 chamada de pipeline
- Etapa 11 → UI única (não 5 páginas)
- Explainability já existe em `/api/intelligence/explanations/<id>`

**Justificativa:** `KnowledgeService.run_pipeline` já orquestra todas as 7 etapas em uma chamada. Não há valor em expor cada etapa como REST separada — o pipeline é a unidade natural de trabalho. Para debug/auditoria, logs do servidor são suficientes.

### 2.6 Permissões

Todas as 7 permissões usadas no plano revisado **já existem** em `araos/platform/identity/permissions.py`. **Nenhuma permissão nova é necessária.**

| Permissão | Já existe? |
|---|:---:|
| `INTELLIGENCE_CORRELATION_READ` | ✅ |
| `INTELLIGENCE_CORRELATION_COMPUTE` | ✅ |
| `INTELLIGENCE_COHORT_READ` | ✅ |
| `INTELLIGENCE_COHORT_DEFINE` | ✅ |
| `INTELLIGENCE_ANALYTICS_READ` | ✅ |
| `EXPLAINABILITY_READ` | ✅ (mas não aplicável a endpoints novos — Explainability é Sprint 4.1) |
| `INTELLIGENCE_TIMELINE_READ` | ✅ (mas não aplicável — Timeline é Sprint 4.1) |

---

## 3. Código que NÃO precisa ser escrito

| Arquivo | Razão para NÃO criar |
|---|---|
| `knowledge/infrastructure/unit_of_work.py` | Session SQLAlchemy + `with` context manager já é UoW. Não há precedente no AraOS. |
| `interfaces/rest/knowledge/explanations.py` | Duplicaria `/api/intelligence/explanations/<id>` |
| `interfaces/rest/knowledge/events.py` | Duplicaria `/api/intelligence/timeline/<patient_id>` |
| `interfaces/rest/knowledge/correlations.py` | Endpoints individuais substituídos por inline em `/genomes/<id>` |
| `interfaces/rest/knowledge/hypotheses.py` | Idem |
| `interfaces/rest/knowledge/graphs.py` | Idem |
| `interfaces/rest/knowledge/research.py` (lista) | Sessões são internas; só `GET /<id>` é útil (replay) |
| `interfaces/rest/knowledge/replay.py` | Replay = executar pipeline de novo → unificar em `/pipelines/run` |
| `frontend/src/pages/knowledge/GraphViewer.js` | Sem lib de grafo; usar lista com chips |
| `frontend/src/pages/knowledge/CohortDashboard.js` | Tab em KnowledgeDashboardPage |
| `frontend/src/pages/knowledge/ResearchReplay.js` | Tab em KnowledgeDashboardPage |
| `frontend/src/pages/knowledge/ExplainabilityDashboard.js` | Duplica UI Sprint 4.1 |
| `frontend/src/pages/knowledge/CorrelationExplorer.js` | Inline em `/genomes/<id>` |
| `frontend/src/components/TimelineEntry.js` | Não usado em RC1 |
| `frontend/src/components/ExplanationPanel.js` | Não usado em RC1 |
| `frontend/src/components/TwinGraph.js` | Não usado em RC1 |
| `frontend/src/components/TwinVisualizer.js` | Não usado em RC1 |
| `frontend/src/components/DataTable.js` | MUI Table direto é suficiente |
| `frontend/src/components/FilterBar.js` | TextField inline é suficiente |
| `frontend/src/components/Wizard.js` | Não necessário |
| `frontend/src/auth/decorators.ts` | `@tenant_required` mínimo via `_resolve_tenant_id()` já em `_helpers.py` |
| `araos/auth/decorators.py` | Tenant resolver já existe em `routes/_helpers.py` |

**Total economizado:** ~16 arquivos não criados.

---

## 4. Componentes que devem ser reaproveitados

### 4.1 Backend Python

| Componente | Local | Para que serve no RC1 |
|---|---|---|
| `KnowledgeService.run_pipeline` | `application/knowledge_service.py` | Lógica do endpoint `/pipelines/run` |
| `KnowledgeRepository` ABC | `infrastructure/repository.py` | Interface do `SQLKnowledgeRepository` |
| `InMemoryKnowledgeRepository` | `infrastructure/in_memory.py` | Para testes |
| `mappers.py` (586 linhas) | `infrastructure/mappers.py` | Serialização lossless |
| `SqlAlchemyClinicalEventStore(autocommit=False)` | `event_store/store.py` | Integração com pipeline UoW |
| `Base` + `AuditFieldsMixin` | `platform/tenant/models.py` | Modelos SQLAlchemy |
| `KnowledgePipelineResult` DTO | `application/dto.py` | Response shape |
| `routes/_helpers.py._resolve_tenant_id()` | `routes/_helpers.py` | Tenant resolution (mínimo) |
| `@jwt_required()` Flask decorator | `flask_jwt_extended` | Auth padrão |
| `Permission.INTELLIGENCE_*` | `platform/identity/permissions.py` | Permissões (catálogo, não aplicação) |

### 4.2 Frontend React

| Componente | Local | Para que serve no RC1 |
|---|---|---|
| `PageHeader` | `components/PageHeader.js` | Header de página |
| `EmptyState` | `components/EmptyState.js` | Empty/loading states |
| `LoadingState` | `components/LoadingState.js` | Spinner/skeleton |
| `ErrorBoundary` | `components/ErrorBoundary.js` | Error catching |
| `GlassCard` | `components/ui/GlassCard.js` | Visual primitive |
| `useConfirm` | `hooks/useConfirm.js` | Confirmação destrutiva |
| `useNotifier` | `hooks/useNotifier.js` | Snackbar/Alert |
| `useAuth()` | `contexts/AuthContext.js` | User identity |
| `useAssociation()` | `contexts/AssociationContext.js` | Tenant (X-Association-ID automático) |
| `api` (axios singleton) | `services/api.js` | HTTP client (interceptors JWT/CSRF/tenant) |
| `neuroService.js` (padrão) | `services/neuroService.js` | Template para `knowledgeApi.js` |

### 4.3 REST DTOs

`KnowledgePipelineResult` (já existe em `application/dto.py`) já embute:
- genome, correlations, hypotheses, graph
- correlation_count, hypothesis_count, graph_node_count, graph_edge_count
- started_at, completed_at

**Sem necessidade de criar** `GenomesListResponse`, `GenomeResponse`, `CorrelationsListResponse`, `CorrelationResponse`, `HypothesesListResponse`, `HypothesisResponse`, `GraphsListResponse`, `GraphResponse`, `SessionsListResponse`, `SessionResponse`, `ExplanationResponse`, `EventsListResponse`, `CorrelationComputeRequest`, `CorrelationComputeResponse`, `CohortDefineRequest`, `ResearchExecuteRequest`, `ReplayRequest`, `ReplayResponse` — todas já coertas pelo DTO existente ou pelos endpoints já implementados.

---

## 5. Simplificações encontradas

### 5.1 Pipeline como unidade atômica

**Antes (plano original):**
```
Cliente: POST /pipelines/run → processa
Cliente: GET /correlations → fetch
Cliente: GET /hypotheses → fetch
Cliente: GET /graphs → fetch
Cliente: GET /explanations → fetch
```

**Depois (revisado):**
```
Cliente: POST /pipelines/run → processa TUDO + persiste
Cliente: GET /genomes/<id> → recebe genome com correlações/hypotheses/graph inline
```

**Economia:** 4 chamadas extras eliminadas; DTO único; menos round-trips; melhor cache-ability.

### 5.2 Reuso do Tenant Resolver Existente

**Antes (plano original — W3.1):**
```
Criar: araos/auth/decorators.py com @tenant_required novo
```

**Depois (revisado):**
```
Reusar: routes/_helpers.py._resolve_tenant_id() (já usado por /api/intelligence/*)
```

**Economia:** 1 arquivo não criado; padronização com rotas Sprint 4.1/4.2.

### 5.3 Explicabilidade: NÃO duplicar

**Antes:** plano propunha `GET /api/knowledge/explanations/<id>`.

**Depois:** cliente chama `/api/intelligence/explanations/<id>` (Sprint 4.1 já tem).

**Economia:** 1 endpoint; 1 página frontend.

### 5.4 Events: NÃO duplicar Timeline

**Antes:** plano propunha `GET /api/knowledge/events`.

**Depois:** cliente chama `/api/intelligence/timeline/<patient_id>` (Sprint 4.1 já tem).

**Economia:** 1 endpoint.

### 5.5 Graph: lista em vez de visualização

**Antes:** plano propunha `KnowledgeGraphViewer.js` (componente gráfico).

**Depois:** KnowledgeDashboardPage renderiza nodes como Cards / Chips em Grid; edges como setas simples (chip → chip).

**Economia:** ~150 linhas de frontend; zero dependências externas.

### 5.6 DTO único para genome

**Antes:** plano propunha `GenomesListResponse`, `GenomeResponse`, `CorrelationsListResponse`, `HypothesisListResponse`, `GraphResponse` (5 DTOs).

**Depois:** reusar `KnowledgePipelineResult` (já tem tudo embutido) ou uma versão simplificada.

**Economia:** 5 DTOs não criados.

---

## 6. Arquivos novos realmente necessários

### 6.1 Backend (3 arquivos novos)

| Arquivo | Linhas estimadas | Conteúdo |
|---|---:|---|
| `araos/clinical/knowledge/infrastructure/sql.py` | ~600 | ORM models + `SQLKnowledgeRepository` |
| `araos/clinical/knowledge/application/composition.py` | ~80 | `knowledge_composition()` context manager |
| `araos/clinical/knowledge/interfaces/__init__.py` | ~10 | Blueprints registry |
| `araos/clinical/knowledge/interfaces/rest.py` | ~300 | 7 endpoints REST |
| `tests/sprint_4_5/conftest.py` | ~80 | Fixtures (pg_engine, session, repos) |
| `tests/sprint_4_5/test_sql_repository.py` | ~250 | CRUD + tenant isolation |
| `tests/sprint_4_5/test_sql_determinism.py` | ~150 | state_hash round-trip |
| `tests/sprint_4_5/test_uow_atomicity.py` | ~100 | Atomicity tests |
| `tests/sprint_4_5/test_rest_endpoints.py` | ~200 | REST tests |
| `tests/sprint_4_5/test_e2e_flow.py` | ~150 | Pipeline end-to-end |
| **Subtotal backend** | **~1.920 linhas** | — |

### 6.2 Frontend (2 arquivos novos)

| Arquivo | Linhas estimadas | Conteúdo |
|---|---:|---|
| `frontend/src/services/knowledgeApi.js` | ~80 | HTTP client (segue `neuroService.js`) |
| `frontend/src/pages/knowledge/KnowledgeDashboardPage.js` | ~600 | 4 tabs + listagens + forms |
| **Subtotal frontend** | **~680 linhas** | — |

### 6.3 Documentação (3 arquivos novos)

| Arquivo | Linhas estimadas | Conteúdo |
|---|---:|---|
| `docs/SQL_REPOSITORY_EQUIVALENCE_REPORT.md` | ~150 | InMemory vs SQL byte-identical |
| `docs/RC1_DELIVERY_REPORT.md` | ~200 | Entrega RC1 |
| `docs/RC1_DEMO_SCRIPT.md` | ~100 | Script de demo E2E |
| **Subtotal docs** | **~450 linhas** | — |

### 6.4 Total

| Categoria | Linhas |
|---|---:|
| Backend | ~1.920 |
| Frontend | ~680 |
| Documentação | ~450 |
| **Total novo** | **~3.050 linhas** |

**Versus plano original: ~5.900 linhas.** **Redução: ~48%.**

---

## 7. Riscos arquiteturais

| # | Risco | Mitigação |
|---|---|---|
| R1 | Composite PK + NO ACTION FKs quebram cascade delete esperado | Aceito pelo G3; LGPD compliance |
| R2 | `result_json` TEXT vs JSONB inconsistência | Documentado em ADR-0008; manter TEXT para bit-identical |
| R3 | DTO único `KnowledgePipelineResult` muito grande para algumas chamadas | Versão simplificada do DTO pode ser criada se profiling mostrar problema |
| R4 | Frontend sem biblioteca de grafo | Aceito para RC1; lista com chips suficiente para demo |
| R5 | `@tenant_required` mínimo pode divergir de produção Hardening | Aceito — produção Hardening cria versão robusta |
| R6 | Pipeline falha parcialmente sem atomicidade real | `knowledge_composition` context manager garante commit/rollback |
| R7 | `execution_options(skip_tenant=True)` não testado em AraOS | Tenant-bound ABC substitui; sem necessidade de usar |
| R8 | hypothesis_id ainda com gap (task #197) | **OBRIGATÓRIO** antes do RC1 |

---

## 8. Nova ordem recomendada

### 8.1 Sequência revisada

```
Fase 1 (CORE):
  1.1. task #197 hypothesis_id fix (0.2 sprint) — CRITICAL
  1.2. sql.py (SQLKnowledgeRepository + ORM models) (1.0 sprint)
  1.3. composition.py (knowledge_composition context manager) (0.2 sprint)
  1.4. test_sql_repository.py + test_sql_determinism.py (0.4 sprint)

Fase 2 (INTEGRAÇÃO REST):
  2.1. interfaces/rest.py (7 endpoints) (0.5 sprint)
  2.2. test_rest_endpoints.py (0.3 sprint)

Fase 3 (INTEGRAÇÃO UI):
  3.1. knowledgeApi.js (0.1 sprint)
  3.2. KnowledgeDashboardPage.js com 4 tabs (0.6 sprint)

Fase 4 (VALIDAÇÃO):
  4.1. test_e2e_flow.py (0.2 sprint)
  4.2. test_uow_atomicity.py (0.2 sprint)
  4.3. demo manual + docs (0.3 sprint)

Subtotal: ~3.5 sprints
```

### 8.2 Ordem por V/R (value/risk ratio)

| Ordem | Tarefa | Valor | Risco | V/R |
|:---:|---|:---:|:---:|:---:|
| 1 | task #197 hypothesis_id | 10 | 9 (segurança) | 1.11 |
| 2 | sql.py SQL repo | 10 | 8 | 1.25 |
| 3 | composition.py | 6 | 5 | 1.20 |
| 4 | REST 7 endpoints | 9 | 4 | 2.25 |
| 5 | KnowledgeDashboardPage | 8 | 5 | 1.60 |
| 6 | Test SQL | 8 | 3 | 2.67 |
| 7 | Test E2E | 10 | 3 | 3.33 |

**Dependências:**
- 2 depende de 1 (fix hypothesis_id antes de persistir)
- 3 depende de 2 (composição precisa do repo)
- 4 depende de 3 (REST precisa da composição)
- 5 depende de 4 (UI consome REST)
- 6 depende de 2 (testa SQL)
- 7 depende de 2, 3, 4, 5 (e2e completo)

**Sequência executável final:** `1 → 2 → 3 → 4 → 5 → 6 → 7`

### 8.3 Marcos (gates de aceitação)

| Marco | Definição de "done" |
|---|---|
| M1 — hypothesis_id fix | pytest passa com tenant_id no composition; manifest updated |
| M2 — SQL repo | test_sql_repository.py + test_sql_determinism.py passam em PostgreSQL real |
| M3 — UoW implícito | composition.py + test_uow_atomicity.py passam |
| M4 — REST | test_rest_endpoints.py passa; tenant isolation validada |
| M5 — UI | KnowledgeDashboardPage renderiza 4 tabs com dados reais |
| M6 — E2E | test_e2e_flow.py passa; demo manual executa sem erros |

---

## 9. Estimativa revisada

| Fase | Plano original | Plano revisado | Economia |
|---|:---:|:---:|:---:|
| Fase 1 (CORE) | ~2.3 sprints | ~1.6 sprints | -30% |
| Fase 2 (REST) | ~1.6 sprints | ~0.8 sprints | -50% |
| Fase 3 (UI) | ~1.3 sprints | ~0.7 sprints | -46% |
| Fase 4 (E2E) | ~0.7 sprints | ~0.5 sprints | -29% |
| **Total** | **~5.9 sprints** | **~3.5 sprints** | **-41%** |

| Métrica | Plano original | Plano revisado | Economia |
|---|---:|---:|---:|
| Endpoints REST | 14+4 | 7 | -57% |
| Páginas frontend | 5 | 1 | -80% |
| Componentes frontend | 9+ | 0 novo | -100% |
| Arquivos Python backend | 12+ | 6 | -50% |
| Linhas de código | ~5.900 | ~3.050 | -48% |
| Sprints | ~5.9 | ~3.5 | -41% |

---

## 10. Classificação de Tech Debt

### 10.1 Obrigatório antes do RC1

| Item | Razão |
|---|---|
| task #197 hypothesis_id cross-tenant | Cross-tenant leak REAL; data integrity |
| migration 0331305d2b3c dead filename | Visível em CI; renomeação trivial |

### 10.2 Pode esperar Production Hardening (pós-RC1)

| Item | Por que não bloqueia RC1 |
|---|---|
| RBAC 106 perms não aplicadas em endpoints | RC1 demo não é produção; JWT + roles são suficientes |
| Tenant unificado (3 mecanismos) | `_resolve_tenant_id()` é funcional; unificação é refactor |
| Audit Ledger AraOS conectado | Logs do servidor bastam para demo |
| Refresh Token Flask | Token de 12h é suficiente para demo de 1 sprint |
| CSRF cross-cutting | Endpoint único `/pipelines/run` POST tem CSRF via helper global |
| MFA TOTP | Demo é local; MFA é UX pós-RC1 |
| SECRET_KEY env var | Demo usa dev secret; produção troca |
| JWT revocation Redis | Single-process demo OK |
| V1/V2 violações (timeline.app→event_store, knowledge.domain→genome.app) | Fundação preservada; ADR-0007 resolve |

### 10.3 Nunca será necessário (Housekeeping)

| Item | Por que |
|---|---|
| Stubs clinical/{graph,twin,summary,projections} | Cleanup post-RC1, não impacta demo |
| Páginas órfãs (NeuroScalesListPage, NeuroScaleApplyPage, IntelligentImportPage) | Cleanup post-RC1 |
| 39 tests debug/fix | Auditoria específica depois |
| Dockerfiles duplicados | Cleanup post-RC1 |
| AraFlow ADRs 001-015 sem arquivos | Cosmético |
| Frontend tests baseline | Pós-RC1, fora do escopo |
| i18n mínimo | RC1 = pt-BR only |
| Schema legacy sem soft delete | Refactor massivo, fora do escopo |

---

## 11. Recomendação Final

> **🟢 Plano revisado com otimizações.**

### 11.1 Decisão

Não reestruturar, apenas cortar. Aprovar esta revisão como plano oficial.

### 11.2 Aprovações necessárias antes de implementar

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Cortar `KnowledgeUnitOfWork` | ✅ APROVAR |
| 2 | Reduzir REST 14 → 7 endpoints | ✅ APROVAR |
| 3 | Reduzir Dashboard 5 → 1 página | ✅ APROVAR |
| 4 | Reduzir E2E 11 → 5 passos | ✅ APROVAR |
| 5 | Reusar `/api/intelligence/*` para explanations/timeline | ✅ APROVAR |
| 6 | Reusar `_resolve_tenant_id()` para tenant | ✅ APROVAR |
| 7 | KnowledgeDashboardPage única com 4 tabs | ✅ APROVAR |
| 8 | Housekeeping DEFERRED pós-RC1 | ✅ APROVAR |
| 9 | Production Hardening DEFERRED pós-RC1 | ✅ APROVAR |

### 11.3 Sequência aprovada para implementação

```
1. task #197 hypothesis_id fix (Foundation obrigatória)
2. sql.py (SQLKnowledgeRepository + 7 ORM models)
3. composition.py (knowledge_composition context manager)
4. test_sql_repository.py + test_sql_determinism.py
5. interfaces/rest.py (7 endpoints)
6. test_rest_endpoints.py
7. knowledgeApi.js
8. KnowledgeDashboardPage.js (4 tabs)
9. test_e2e_flow.py + test_uow_atomicity.py
10. RC1_DEMO_SCRIPT.md + RC1_DELIVERY_REPORT.md
```

**Estimativa: ~3.5 sprints** com reuso máximo e Foundation Freeze preservada.

---

## 12. Veredicto Final

> **Plano revisado com otimizações.**
>
> Redução de **48% no código novo**, **41% nos sprints**, **57% nos endpoints REST**, **80% nas páginas Dashboard**.
>
> Sem expansão de domínio. Sem novos bounded contexts. Sem novas permissões. Sem novos componentes visuais.
>
> Apenas infraestrutura + integração, preservando o patrimônio de código existente.

---

**Aprovações pendentes:**
- Aprovação do usuário para iniciar Fase 1.1 (task #197 hypothesis_id fix)
- Confirmação dos cortes propostos

**Ver também:**
- [RC1_READINESS_REPORT.md](RC1_READINESS_REPORT.md) — versão anterior
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
- [araos-rc1-pivot](araos-rc1-pivot.md) (memory)
