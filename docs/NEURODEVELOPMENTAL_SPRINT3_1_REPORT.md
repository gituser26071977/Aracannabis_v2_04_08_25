# Sprint 3.1 — Clinical Event Engine (Foundation)

**Status:** ✅ Entregue
**Data:** 2026-07-16
**Sprint pai:** Módulo NEURODESENVOLVIMENTO · Sprint 3 (registry + catalog + timeline)
**ADR:** [ADR-0001](../adr/0001-clinical-event-engine.md)
**Branch:** `fix/p0-stabilization-2026-06`

---

## 1. Resumo executivo

Sprint 3.1 entregou o **Clinical Event Engine**, fundação arquitetural cross-specialty do AraOS. A partir desta sprint, todo evento clínico de qualquer especialidade (Neuro, Cannabis, Fisio, Fono, TO, Psicologia, Psiquiatria, UTI, Dor, Sono, Reabilitação) flui por uma única tabela `clinical_events`, com hash chain SHA-256 e ordenação canônica por sequence per-tenant.

**Métricas:**

| Indicador | Valor |
|---|---|
| Linhas backend (código de produção) | ~620 LOC |
| Linhas de teste | ~1.350 LOC |
| Testes | **239 (100%)** |
| Cobertura | **99%** (target ≥95%) |
| Event types catalogados | 26 (cross-specialty) |
| Migração Alembic | 1 (`2026_07_15_cee_s31`) |
| ADR | [ADR-0001](../adr/0001-clinical-event-engine.md) |

---

## 2. Decisões arquiteturais materializadas

### D1 — Event Store cross-specialty ✅
- Tabela única `clinical_events` (PostgreSQL/SQLite)
- 12+ specialties escrevem no mesmo store via `ClinicalEventPublisher`
- Campo `source_module` separa domínios

### D2 — Coexistência Event Store + Event Bus ✅
- Store persiste (authoritative source)
- Bus notifica (Redis Streams, fan-out em tempo real)
- `ClinicalEventPublisher.publish()` chama store primeiro, depois bus (graceful degradation se bus falhar)
- **Não** existe EventBus2 — store e bus têm papéis distintos

### D3 — Migração dual-write com consistency check diário
- Migration cria `clinical_events` + `clinical_event_sequences`
- Tabelas legadas (`neuro_*`, `cannabis_*`) **não tocadas** nesta sprint
- Próxima sprint (3.2) inicia dual-write com check diário

### D4 — Conditions Catalog global ✅
- `CLINICAL_EVENT_CATALOG` com 26 event types cobrindo diagnósticos, escalas, medicações, terapias, sono, peso, altura, crises, hospitalizações, cirurgias, exames, consultas, family meetings, care plans
- Versionamento por `event_version` (default "1.0")
- Schema validation via JSON Schema Draft 7

### D5 — Phenotypes com `source_event_ids`
- Ainda não implementado (Sprint 3.5)
- Schema já preparado: `aggregate_type` + `aggregate_id` permitem reconstruir fenótipos

### Decisão adicional: `sequence` per-tenant (insertion order)

Durante o desenvolvimento, identificamos que ordenar a chain por `event_datetime` (clinical time) é semanticamente errado:

- `event_datetime` é **atributo do payload** — pode ser backdated, batch-imported, registrado com delay
- A chain deve refletir **insertion order** (quando o sistema tomou conhecimento)

Solução: coluna `sequence BIGINT NOT NULL` + tabela tracker `clinical_event_sequences(tenant_id PK, last_sequence)`. Atomicamente alocada via `SELECT ... FOR UPDATE` (PostgreSQL) ou serialização natural (SQLite).

```sql
-- Índice para hot path do hash chain
CREATE INDEX ix_clinical_events_tenant_sequence ON clinical_events (tenant_id, sequence);
-- Integridade adicional: unicidade da sequence por tenant
ALTER TABLE clinical_events ADD CONSTRAINT uq_clinical_events_tenant_sequence UNIQUE (tenant_id, sequence);
```

---

## 3. Componentes entregues

### 3.1. Pacote `araos.clinical.event_store`

| Arquivo | LOC | Responsabilidade |
|---|---|---|
| `__init__.py` | 50 | API pública (exports) |
| `catalog.py` | 150 | Catálogo versionado de 26 event types |
| `hash_chain.py` | 100 | SHA-256 utilities: compute, verify, find_break |
| `models.py` | 220 | `ClinicalEventModel` + `ClinicalEventSequence` (SQLAlchemy 2.0) |
| `publisher.py` | 130 | `ClinicalEventPublisher` (validate + write + fan-out) |
| `store.py` | 470 | `ClinicalEventStore` (ABC) + InMemory + SqlAlchemy impls |
| `validators.py` | 80 | JSON Schema Draft 7 validation |
| `migrations/2026_07_15_cee_s31.py` | 130 | Criação de `clinical_events` + `clinical_event_sequences` |

### 3.2. Testes

| Arquivo | Testes | Cobertura |
|---|---|---|
| `tests/clinical_event_store/test_catalog.py` | 50+ (parametrized) | 98% |
| `tests/clinical_event_store/test_hash_chain.py` | 22 | 97% |
| `tests/clinical_event_store/test_models.py` | 14 | 100% |
| `tests/clinical_event_store/test_publisher.py` | 18 | 100% |
| `tests/clinical_event_store/test_store.py` | 53 (InMemory) | 99% |
| `tests/clinical_event_store/test_store_sqlalchemy.py` | 47 (PostgreSQL/SQLite) | 99% |
| `tests/clinical_event_store/test_store_helpers.py` | 22 | 100% |
| `tests/clinical_event_store/test_validators.py` | 13 | 100% |
| **TOTAL** | **239 (100%)** | **99%** |

### 3.3. Event Catalog (26 tipos)

**PATIENT** (2): `PATIENT_CREATED`, `PATIENT_UPDATED`

**DIAGNOSIS** (4): `DIAGNOSIS_ADDED`, `DIAGNOSIS_REMOVED`, `DIAGNOSIS_UPDATED`, `DIAGNOSIS_STATUS_CHANGED`

**SCALE** (2): `SCALE_APPLIED`, `SCALE_UPDATED`

**MEDICATION** (3): `MEDICATION_STARTED`, `MEDICATION_ADJUSTED`, `MEDICATION_STOPPED`

**CANNABIS** (1): `CANNABIS_ADJUSTED`

**THERAPY** (2): `THERAPY_STARTED`, `THERAPY_FINISHED`

**SCHOOL** (1): `SCHOOL_CHANGED`

**SLEEP/WEIGHT/HEIGHT** (3): `SLEEP_CHANGED`, `WEIGHT_CHANGED`, `HEIGHT_CHANGED`

**CRISIS** (1): `CRISIS_RECORDED`

**CLINICAL_FACT** (4): `HOSPITALIZATION`, `SURGERY`, `LABORATORY_RESULT`, `IMAGING_RESULT`

**CONSULTATION** (1): `CONSULTATION_PERFORMED`

**OTHER** (2): `FAMILY_MEETING`, `CARE_PLAN_UPDATED`

Cada entry tem: `code`, `name`, `description`, `version`, `producer` (enum), `status` (active/deprecated), `json_schema` (Draft 7).

---

## 4. Garantias técnicas

### 4.1. Append-only
- Toda correção = novo evento (`DIAGNOSIS_REMOVED` ao invés de DELETE; `SCALE_UPDATED` ao invés de UPDATE)
- Soft delete via `deleted_at` (LGPD)
- Sem `UPDATE clinical_events` em produção

### 4.2. Hash chain SHA-256
- `event_hash = SHA256(previous_hash + canonical_json(event))`
- Canonical JSON: `sort_keys=True, separators=(",", ":"), default=str`
- Verificação O(N) via `verify_chain(events)`
- `find_break(events)` localiza índice da primeira corrupção

### 4.3. Multi-tenant isolation
- Toda tabela tem `tenant_id` FK → `araos_organizations.id` (CASCADE)
- `clinical_event_sequences` é PK em `tenant_id` (1 linha por tenant)
- `last_hash(tenant_id)`, `verify_chain(tenant_id, patient_id?)` — chain sempre per-tenant

### 4.4. Thread safety (InMemory)
- `threading.RLock` (re-entrante) protege `append() ↔ last_hash()` recursão

### 4.5. Sequence atomicity (SqlAlchemy)
- PostgreSQL: `SELECT ... FOR UPDATE` em `clinical_event_sequences`
- SQLite: serialização natural da Session

### 4.6. Wildcard queries
- `event_types=["DIAGNOSIS_*"]` casa com `DIAGNOSIS_ADDED`, `DIAGNOSIS_REMOVED`, etc.
- Semântica SQL LIKE (`*` inclui sequência vazia)

---

## 5. Compatibilidade

| Banco | Suportado | Notas |
|---|---|---|
| PostgreSQL 14+ | ✅ Production | `SELECT FOR UPDATE` para sequence |
| SQLite (in-memory / file) | ✅ Tests | Sequence alocada em transação |
| MySQL 8+ | ⚠️ Pendente teste | Pode precisar de `SELECT FOR UPDATE` adjustment |

| ORM | Suportado | Notas |
|---|---|---|
| SQLAlchemy 2.0+ (declarative) | ✅ | `Mapped[]`, `mapped_column()` |
| Flask-SQLAlchemy | ⚠️ Não testado | Adapter provavelmente necessário |

---

## 6. Princípios arquiteturais registrados (ADR-0001)

1. **Clinical Event = Unidade Fundamental**
2. **Projection First** (read models são descartáveis)
3. **Event Catalog versionado**
4. **Coexistência Event Store + Event Bus**
5. **Migração dual-write com consistency check**
6. **Conditions Catalog global**
7. **Phenotypes com `source_event_ids`**

Mais a nova decisão: **sequence per-tenant = ordem canônica da chain** (insertion order, não clinical time).

---

## 7. Pendências / Próxima sprint

### Sprint 3.2 — Neurodevelopmental Registry
- Adapter que traduz `neuro_*` legado → `ClinicalEventPublisher`
- Dual-write: tabela legada continua existindo, novos eventos vão para `clinical_events`
- Consistency check diário (cron ou Celery beat): comparar contagens

### Sprint 3.3 — Conditions Catalog (broader clinical catalog)
- Catálogo versionado de condições (não apenas diagnósticos)
- Cobre: fenótipos, fatores de risco, síndromes, comorbidades, biomarcadores, classificações funcionais
- Cada condição vira `event_type` no catalog

### Sprint 3.4 — Timeline read model
- Projection: rebuilda `araos_clinical_timeline_entries` a partir de `clinical_events`
- Sort por `event_datetime DESC` (clinical time) — view de timeline clínica

### Sprint 3.5 — Longitudinal Phenotypes
- Snapshot materializado: `REDACTED`
- `source_event_ids` lista — rastreabilidade completa
- Rebuildable from Event Store

### Sprint 3.6 — Escalas finais
- ABC, PSQI, AQ, Conners (4 escalas)
- Cada uma persiste como `SCALE_APPLIED` event no store
- Auto-registro no plugin registry

---

## 8. Lições aprendidas

1. **Decisão arquitetural > conveniência**: ordenar chain por `event_datetime` parecia natural, mas é semanticamente errado. `sequence` é a verdade de registro.

2. **Testes SQLite expõem premissas falsas**: a imprecisão de 1 segundo do SQLite para `DateTime` forçou a decisão de `sequence`. Em produção (PostgreSQL) poderia passar despercebido por anos.

3. **Timezone-awareness é responsabilidade da aplicação, não do banco**: SQLite strippa `tzinfo` no round-trip. `_isoformat_utc()` garante formato idêntico independente do storage.

4. **RLock > Lock**: `append() → last_hash()` é re-entrante. `threading.Lock` causava deadlock nos testes de concorrência.

5. **Catálogo versionado ANTES de producers**: começar pelo catálogo (não pelo código) forçou clareza sobre schema, versionamento, compatibilidade.

---

## 9. Comandos de verificação

```bash
# Rodar suite completa
pytest tests/clinical_event_store/ -v --cov=araos/clinical/event_store --cov-fail-under=95

# Verificar migration
alembic upgrade head  # cria clinical_events + clinical_event_sequences
alembic downgrade -1  # rollback

# Smoke test InMemory
python -c "
from araos.clinical.event_store import InMemoryClinicalEventStore, ClinicalEventPublisher
store = InMemoryClinicalEventStore()
publisher = ClinicalEventPublisher(store=store)
eid = publisher.publish(
    tenant_id='t-1', patient_id='p-1',
    event_type='SCALE_APPLIED',
    payload={'scale_code': 'GAD7', 'total_score': 5},
)
print('Event ID:', eid)
print('Chain valid:', store.verify_chain('t-1'))
"
```

---

## 10. Aprovação

- [x] 239 testes passando
- [x] Cobertura 99% (target ≥95%)
- [x] Migration Alembic criada
- [x] ADR-0001 atualizado com decisão `sequence`
- [x] Catálogo com 26 event types
- [ ] **Aprovação humana** para Sprint 3.2

---

**Próxima ação**: aguardando aprovação humana para iniciar **Sprint 3.2 — Neurodevelopmental Registry** (adapter que dual-writes eventos Neuro no Event Store).