# MODULE_DEPENDENCY_REPORT.md — Relações entre Módulos e Bounded Contexts

**Data:** 2026-07-22
**Escopo:** read-only — catalogação de dependências internas e externas.

---

## 1. Mapa de Bounded Contexts (BC) sob Architecture Freeze v1.0

### 1.1 Core (7 BCs + 2 auxiliares)

| BC | Status | Aggregate Roots | Projections | Domain Services | Application Services |
|---|---|:---:|:---:|:---:|:---:|
| ClinicalEventStore | 🟢 FROZEN | — | — | append, query, replay | ClinicalEventService |
| NeuroRegistry | 🟢 FROZEN | ClinicalIdentity | RegistryProjection | 7× domain services | 6× app services |
| ContextEngine | 🟡 Proposto ADR-0003 | ClinicalContext | Active, Relationship | RuleEngine, ContextSuggester | ClinicalContextService, ClinicalContextQuery |
| GenomeEngine | 🟢 ACCEPTED (ADR-0005) | ClinicalGene (AR) | GenomeProjection | ReplayEngine, RuleEngine | GeneService, KnowledgePreface |
| KnowledgeEngine | 🟡 Foundation Only | ClinicalGenome (AR) | GraphProjection | CorrelationService, HypothesisService | KnowledgeService |
| Timeline | 🟢 Sprint 4.1 | — | TimelineProjection | TimelineQuery | TimelineService |
| Explainability | 🟢 Sprint 4.1 | Explanation (VO) | — | ExplanationRegistry | ExplainabilityService |

**Auxiliares:** Platform (tenant/identity/audit/contracts) + Integration.

### 1.2 Edges DAG (sem ciclos)

24 edges oficiais declarados em ARCHITECTURE_FREEZE_DEPENDENCY_MAP.md.

**Violações registradas (V1, V2) deferidas:**

| Código | Edge | Severidade | Status |
|---|---|---|---|
| V1 | `clinical.timeline.app.query → event_store.store` (manifest re-exporta append) | 🟠 High | ADR-0007 pendente |
| V2 | `knowledge.domain → genome.app.ReplayEngine` | 🟠 High | ADR-0007 pendente |

## 2. Dependências Internas

### 2.1 Por pacote araos/

| Pacote | BC | Depende de (interno) | Depende de (externo) |
|---|---|---|---|
| araos/agents/ | runtime | platform.contracts, platform.event_bus, platform.audit | — |
| araos/clinical/entities | entities | — | dataclasses |
| araos/clinical/event_store | event_store | platform.tenants, platform.identity | sqlalchemy, hashlib |
| araos/clinical/timeline | timeline | event_store, observability | dataclasses |
| araos/clinical/observability | observability | — | prometheus_client, logging |
| araos/clinical/contracts | contracts | platform.contracts | abc |
| araos/clinical/context | context | event_store, timeline, observability, explainability | sqlalchemy |
| araos/clinical/explainability | explainability | platform.audit | dataclasses |
| araos/clinical/genome | genome | event_store, observability, explainability, timeline | sqlalchemy |
| araos/clinical/knowledge | knowledge | genome, explainability, event_store | sqlalchemy |
| araos/clinical/{graph,twin,projections,summary} | LEGACY | — | — |
| araos/demo/ | demo | clinical.* + platform.identity | Flask |
| araos/followup/ | followup | event_store, timeline, explainability | sqlalchemy |
| araos/integration/ | integration | platform.contracts, platform.event_bus | — |
| araos/intelligence/ | intelligence | — | openai, zhipu, crewai |
| araos/knowledge/ | knowledge | intelligence/embeddings | (não confundir com clinical/knowledge) |
| araos/platform/api | api | platform.identity, platform.audit | Flask |
| araos/platform/audit | audit | platform.identity, platform.tenants | sqlalchemy |
| araos/platform/contracts | contracts | — | abc |
| araos/platform/event_bus | event_bus | platform.contracts, platform.audit | — |
| araos/platform/events | events | — | — |
| araos/platform/feature_flags | flags | platform.tenants | — |
| araos/platform/identity | identity | platform.tenants | bcrypt, jwt, PyJWT |
| araos/platform/sdk | sdk | platform.identity | — |
| araos/platform/shared | shared | platform.tenants | — |
| araos/platform/tenant | tenant | platform.identity | sqlalchemy |
| araos/specialties/cannabis | cannabis | legacy SIAP models + araos.platform.identity | Flask |
| araos/specialties/core | core | — | — |
| araos/specialties/neurodevelopmental | neuro | clinical.event_store, clinical.timeline, clinical.genome | Flask |

### 2.2 Camadas DDD por BC (genome como referência)

```
clinical.genome/
├── domain/
│   ├── clinical_gene.py        # AR + GeneExpression VO + invariantes
│   ├── correlation.py
│   ├── explainability.py
│   ├── hypothesis.py
│   ├── knowledge_graph.py
│   └── replay_engine.py        # V2 violação: import cross-domain
├── application/
│   ├── gene_service.py
│   ├── gene_registry_service.py
│   ├── correlation_service.py
│   ├── hypothesis_service.py
│   ├── graph_service.py
│   ├── cohort_service.py
│   ├── research_service.py
│   ├── knowledge_service.py
│   ├── dto.py
│   └── composition.py          # W2.1 injetado
└── infrastructure/
    ├── repository.py           # ABC tenant-bound (G3)
    ├── in_memory.py            # InMemory implementation
    ├── sql.py                  # SQLKnowledgeRepository (W1.3 — pendente)
    ├── unit_of_work.py         # UoW (W1.5 — pendente)
    └── mappers.py              # lossless entity↔dict
```

## 3. Dependências Externas

### 3.1 Python core

| Lib | Versão | Onde | Uso |
|---|---|---|---|
| Flask | ~2.x | raiz | Web framework legado |
| flask-jwt-extended | — | routes/auth.py | Auth profissional/paciente |
| Flask-SQLAlchemy | — | raiz | ORM legado (db.Model) |
| SQLAlchemy | 2.0 | araos/clinical/* | ORM declarativo |
| Alembic | — | migrations | Schema migration |
| PyJWT | — | araos/platform/identity | Tokens |
| bcrypt | NÃO instalado | — | password hashing ausente (usa Werkzeug) |
| Werkzeug security | latest | routes/auth.py | PBKDF2-SHA256 100k |
| Flask-Limiter | — | app_cors_livre.py | Rate limit |
| Hypothesis | — | sprint_4_4_5 | Property-based testing |
| prometheus_client | — | clinical/observability | Metrics |
| spacy | — | intelligence/ | NER (opcional) |
| openai | — | intelligence/ | LLM |
| zhipuai | — | intelligence/ | LLM altern. |
| crewai | — | intelligence/ | Agent orchestration |
| zhipu | — | intelligence/ | Embeddings |
| ldap3 | — | aap.py | LDAP auth |
| sendgrid | — | notifications | Email |
| MercadoPago SDK | — | mercadopago.py | Billing |
| Locust | — | scripts/loadtest | Load test |

### 3.2 JavaScript frontend

| Lib | Versão |
|---|---|
| React | 18.2 |
| react-router-dom | 6.22 |
| @mui/material | 5.15 |
| @mui/x-date-pickers | 8.4 |
| @emotion/react, @emotion/styled | 11.11 |
| axios | 1.6 |
| chart.js | 4.4 |
| recharts | 2.15 |
| moment | — |
| date-fns | — |
| react-dropzone | 14.2 |
| @fullcalendar/* | 6.1 |
| react-scripts (CRA) | 5.0.1 |

## 4. Cruzamentos Críticos (cross-BC)

### 4.1 Knowledge → Genome (legítimo via domain)
- `KnowledgeService.build_genome_from_genes` importa `ClinicalGene` de `araos/clinical/genome`
- Result: ClinicalGenome é agregado externo para o BC Knowledge

### 4.2 Knowledge → EventStore (legítimo)
- `KnowledgeService.build_genome_from_events` importa `DomainEvent` de `araos/clinical/genome` (que veio de event_store)
- Não acessa store diretamente

### 4.3 Timeline → EventStore (legítimo, V1 registrada)
- `timeline/app/query.py:23` importa `append` de `event_store/store.py` (store, não domain)
- V1 declarado — re-exporta função de infrastructure

### 4.4 Context → Timeline + EventStore (legítimo)
- ClinicalContextQuery ativos durante windows do Timeline
- ClinicalContextService emite DomainEvent via event_store

### 4.5 Identity providers (divergente)
- **Flask** (legado) — `flask-jwt-extended`
- **AraOS** (novo) — `araos/platform/identity/tokens.py` (HS256 + refresh 30d)
- Coexistem sem adapter unificado

### 4.6 Tenant resolvers (divergente)
- **Flask middleware** (`tenant_middleware.py`)
- **Helpers Sprint 4** (`_helpers.py`)
- **Platform resolver** (`platform/tenant/*`)
- 3 mecanismos de resolução paralelos

## 5. Diagrama Simplificado (ASCII)

```
┌───────────────────────────── PLATFORM LAYER ─────────────────────────────┐
│  identity  audit  contracts  event_bus  feature_flags  tenant  sdk       │
└──────┬───────────────┬──────────────┬───────────────┬─────────────────────┘
       │               │              │               │
       │               ▼              ▼               ▼
┌──────┴──────────────────────────────────────────────────────────────────┐
│                        CLINICAL BCs (Core)                               │
│                                                                         │
│  event_store ◀───── timeline ◀───── context ◀───── explainability       │
│      ▲                                ▲                                   │
│      │                                │                                   │
│      │                            genome ◀────── knowledge               │
│      │                                │                                   │
│      └─────── neuro_registry ─────────┘                                   │
└─────────────────────────────────────────────────────────────────────────┘
       │                                               │
       ▼                                               ▼
┌─────────────────────┐                    ┌──────────────────────────────┐
│   specialties/      │                    │   integration/               │
│   cannabis          │                    │   adapters                   │
│   neuro             │                    │   event consumers            │
│   core              │                    │   voice                      │
└─────────────────────┘                    └──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LEGACY SIAP (Flask app)                              │
│   routes/* (57 blueprints) — services/* — models.py                      │
└─────────────────────────────────────────────────────────────────────────┘
```

## 6. Acoplamentos Problemáticos (alto fan-in/fan-out)

| Módulo | Fan-in | Fan-out | Observação |
|---|:---:|:---:|---|
| `platform.identity.permissions` | 0 | 1 | 106 permissões catalogadas, ZERO aplicação |
| `platform.audit.ledger` | 0 | 2 | ledger central sem integração |
| `_helpers.py` (Sprint 4) | 0 | 0 | única entrada cross-cutting |
| `tenant_middleware.py` | baixo | médio | engole exceções |
| `models.py` legado | alto | baixo | 1791 linhas, 31 classes |
| `app_cors_livre.py` | — | — | registra 57 blueprints |

## 7. Observações Arquiteturais

- **Foundation Freeze respeitada**: nenhum import de `domains/*` de módulos `infrastructure/*` foi adicionado.
- **DAG sem ciclos**: 24 edges declarados em `ARCHITECTURE_FREEZE_DEPENDENCY_MAP.md`.
- **V1 e V2 proteladas**: ambas referenciam `clinical/` mas suas correções exigem ADR (Foundation Freeze veta modificações ad-hoc).
- **Tenant triplicado**: 3 mecanismos paralelos criados (Flask, helpers, Platform) — convergência requer ADR-0007 ou sprint dedicado.

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [DEAD_CODE_REPORT.md](DEAD_CODE_REPORT.md)
- [BACKEND_AUDIT.md](BACKEND_AUDIT.md)
