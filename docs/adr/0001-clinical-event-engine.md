# ADR-0001: Clinical Event Engine — Event Sourcing + CQRS

| | |
|---|---|
| **Status** | ✅ Accepted |
| **Data** | 2026-07-15 |
| **Autor** | Claude (M3) · revisado e aprovado por arquitetura sênior AraOS |
| **Decisor** | Arquiteto-chefe AraOS |
| **Impacto** | Cross-specialty · plataforma inteira |
| **Substitui** | Premissa antiga de "cada módulo escreve direto na Timeline" |

---

## 1. Contexto

O AraOS acumulou, ao longo de 5 sprints (Foundation → Specialties → Clinical Intelligence), uma premissa implícita que se tornou gargalo arquitetural:

> "Cada módulo clínico escreve diretamente em suas próprias tabelas; a Timeline agrega via `ClinicalProjectionEngine`."

Consequências observadas:

- **Duplicação de lógica** — Cannabis, Neuro, Fisio, Fono, Psicologia cada um com sua própria timeline médica.
- **Auditoria fragmentada** — hash chain existe, mas cobre apenas a tabela auditada, não a totalidade da história clínica.
- **Dashboards/IA acoplados a tabelas** — qualquer mudança de schema quebra 5+ consumidores.
- **Reconstrução de prontuário impossível** — não há como responder "tudo que aconteceu com o paciente entre 2018-01-01 e 2024-12-31".
- **Observatório Sergipano exige ETL frágil** — extrai de N tabelas heterogêneas.

Análise comparada com OpenEHR (modelo dual), FHIR `AuditEvent` (event sourcing nativo) e Epic Chronicles (event log distribuído) confirmou a direção:

> **Tratar o evento clínico como unidade fundamental do sistema.**

---

## 2. Decisão

A partir de 2026-07-15, o AraOS adota **Event Sourcing + CQRS** no núcleo clínico:

### 2.1. Camadas

| Camada | Responsabilidade | Tecnologia |
|---|---|---|
| **Clinical Event Store** (NOVO) | Persistência append-only, hash chain, replay, query | PostgreSQL `clinical_events` |
| **Event Bus** (EXISTENTE) | Fan-out em tempo real, WebSocket, IA live, dashboards live | Redis Streams via `AraOSEventBus` |
| **Projections** (read models) | Read-optimized, descartáveis, rebuildable | PostgreSQL (múltiplas tabelas) |
| **Consumers** | Dashboards, IA, Relatórios, Observatório, Pesquisa | SQL query sobre Event Store ou projections |

**Regra de ouro**: nenhum módulo escreve diretamente em read model. Todo conhecimento nasce como evento.

### 2.2. Princípios arquiteturais (não-negociáveis)

1. **Clinical Event = Unidade Fundamental** — nenhum componente clínico produz informação diretamente para dashboards, IA ou relatórios. Todo o restante consome Clinical Events.

2. **Projection First** — toda tabela de leitura é descartável, reconstruível a partir do Event Store. Nenhuma projeção é fonte primária.

3. **Event Catalog versionado** — cada `event_type` possui:
   - nome
   - descrição
   - versão do schema
   - JSON Schema
   - produtor
   - consumidores
   - compatibilidade
   - status (ativo | depreciado)

4. **Coexistência Event Store + Event Bus** — store persiste, bus notifica. Não existe EventBus2.

5. **Migração em duas fases** (dual-write com consistency check diário) — somente após N ciclos consecutivos sem divergência a tabela legada vira projection read-only.

6. **Conditions Catalog global** — não apenas diagnósticos; cobre fenótipos, fatores de risco, síndromes, biomorbidades, biomarcadores, classificações funcionais.

7. **Phenotypes com `source_event_ids` (lista)** — fenótipo pode derivar de N eventos; rastreabilidade completa preservada.

### 2.3. Schema canônico — tabela `clinical_events`

```sql
CREATE TABLE clinical_events (
    id              UUID PRIMARY KEY,
    tenant_id       VARCHAR(36) NOT NULL REFERENCES araos_organizations(id),
    patient_id      VARCHAR(36) NOT NULL,
    event_type      VARCHAR(64) NOT NULL,           -- ref ao _EVENT_CATALOG
    event_version   VARCHAR(16) NOT NULL DEFAULT '1.0',
    event_datetime  TIMESTAMP NOT NULL,             -- quando aconteceu clinicamente (atributo do payload)
    source_module   VARCHAR(32) NOT NULL,           -- 'neurodevelopmental', 'cannabis', ...
    payload         JSON NOT NULL,                  -- dados específicos
    metadata        JSON NOT NULL DEFAULT '{}',     -- correlation_id, causation_id, tags
    aggregate_type  VARCHAR(32),                    -- 'scale', 'medication', 'diagnosis'
    aggregate_id    VARCHAR(36),                    -- id do objeto afetado
    -- ator (clínico + sistema distintos)
    created_by      VARCHAR(36),                    -- ator clínico (médico, fono, ...)
    created_by_user VARCHAR(36),                    -- user account que executou
    -- audit (AuditFieldsMixin)
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    updated_at      TIMESTAMP,
    deleted_at      TIMESTAMP,                      -- soft delete (LGPD)
    -- hash chain
    previous_hash   VARCHAR(64),                    -- sha256 do evento anterior
    event_hash      VARCHAR(64) NOT NULL,           -- sha256(prev_hash + canonical(event))
    sequence        BIGINT NOT NULL,                -- monotonic per-tenant (insertion order)
    INDEX ix_tenant_patient_dt (tenant_id, patient_id, event_datetime DESC),
    INDEX ix_event_type (event_type),
    INDEX ix_aggregate (aggregate_type, aggregate_id),
    INDEX ix_source_module (source_module, event_datetime),
    INDEX ix_tenant_sequence (tenant_id, sequence),
    UNIQUE CONSTRAINT uq_tenant_sequence (tenant_id, sequence)
);

CREATE TABLE clinical_event_sequences (
    tenant_id       VARCHAR(36) PRIMARY KEY REFERENCES araos_organizations(id),
    last_sequence   BIGINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP
);
```

### 2.3.1. `sequence` — ordem canônica da chain (insertion order, não clinical time)

Decisão arquitetural: **a hash chain é ordenada por `sequence` (insertion order), não por `event_datetime` (clinical time)**.

Por quê:

1. **`event_datetime` é atributo do payload**, não verdade de registro. Pode ser:
   - backdated (evento retroativo: "diagnóstico de 2018 registrado hoje")
   - batch-imported (migração de dados legados)
   - registrado com delay (ex.: paciente traz exame de 3 meses atrás)
2. **`sequence` é a verdade imutável** de "quando o sistema tomou conhecimento do evento".
3. Chain deve ser determinística — independente de imprecisão de timestamp (SQLite: 1s; PostgreSQL: 1µs; ambos perdem precisão em escrita concorrente massiva).
4. Permite UNIQUE constraint `(tenant_id, sequence)` → integridade adicional da chain.

`clinical_event_sequences` é tabela de tracker (1 linha por tenant) com `last_sequence BIGINT`. Atualizada atomicamente via `SELECT ... FOR UPDATE` (PostgreSQL) ou serialização natural (SQLite).

### 2.4. Eventos de domínio iniciais (Sprint 3.1)

Modelo de nomes: `DOMAIN_ACTION`. Compatível com `_EVENT_CATALOG` existente.

| event_type | producer (source_module) | consumers |
|---|---|---|
| `PATIENT_CREATED` | core | audit, knowledge, concierge |
| `PATIENT_UPDATED` | core | audit, knowledge |
| `DIAGNOSIS_ADDED` | core/neuro | audit, timeline, knowledge, observatory_etl |
| `DIAGNOSIS_REMOVED` | core/neuro | audit, timeline |
| `DIAGNOSIS_UPDATED` | core/neuro | audit, timeline |
| `DIAGNOSIS_STATUS_CHANGED` | core/neuro | audit, timeline |
| `SCALE_APPLIED` | neuro | audit, timeline, knowledge, observatory_etl |
| `SCALE_UPDATED` | neuro | audit, timeline |
| `MEDICATION_STARTED` | core/any | audit, timeline, dashboard_cache |
| `MEDICATION_ADJUSTED` | core/any | audit, timeline |
| `MEDICATION_STOPPED` | core/any | audit, timeline |
| `CANNABIS_ADJUSTED` | cannabis | audit, timeline |
| `THERAPY_STARTED` | any | audit, timeline |
| `THERAPY_FINISHED` | any | audit, timeline |
| `SCHOOL_CHANGED` | any | audit, timeline |
| `SLEEP_CHANGED` | any | audit, timeline, phenotypes |
| `WEIGHT_CHANGED` | any | audit, timeline, phenotypes |
| `HEIGHT_CHANGED` | any | audit, timeline, phenotypes |
| `CRISIS_RECORDED` | any | audit, timeline, observatory_etl |
| `HOSPITALIZATION` | any | audit, timeline, observatory_etl |
| `SURGERY` | any | audit, timeline |
| `LABORATORY_RESULT` | core | audit, timeline |
| `IMAGING_RESULT` | core | audit, timeline |
| `CONSULTATION_PERFORMED` | core | audit, timeline, knowledge |
| `FAMILY_MEETING` | any | audit, timeline |
| `CARE_PLAN_UPDATED` | any | audit, timeline |

Adicionar novo `event_type` = nova entrada no `_EVENT_CATALOG` + nova factory function. Zero migração Alembic.

### 2.5. Fluxo de escrita

```
[Application Service]
    │
    ▼
[ClinicalEventPublisher.publish(event_type, payload, ...)]
    │
    ├──→ 1. Validate against _EVENT_CATALOG (schema, version)
    │
    ├──→ 2. Build EventEnvelopeV2 (canonical form)
    │
    ├──→ 3. Compute event_hash = SHA256(prev_hash + canonical(event))
    │
    ├──→ 4. INSERT INTO clinical_events (atomic)
    │
    ├──→ 5. AraOSEventBus.publish()  ──→  Redis Streams fan-out
    │                                          │
    │                                          ├──→ IA live
    │                                          ├──→ Dashboards live (WebSocket)
    │                                          ├──→ Notifications
    │                                          └──→ (futuro) ML streaming
    │
    └──→ 6. Return event_id
```

Dual-write (Sprint 3.1 a Sprint 3.3): para `ScaleApplied`, o sistema também atualiza `neuro_scale_responses` (projection legada). Consistency check diário compara divergências.

### 2.6. Fluxo de leitura — Query API

```python
# Timeline clínica (read model sobre Event Store)
events = await event_store.query(
    tenant_id, patient_id,
    event_types=["DIAGNOSIS_*", "MEDICATION_*", "SCALE_*", "THERAPY_*", ...],
    since=datetime(2018, 1, 1),
    until=datetime(2024, 12, 31),
    order_by="event_datetime ASC"
)

# IA / Observatório
events = await event_store.query(
    tenant_id, patient_id,
    aggregate_type="scale",
    aggregate_id="<scale_id>"
)

# Replay
events = await event_store.replay(
    tenant_id, patient_id,
    since_event_id="..."
)
```

### 2.7. Camadas futuras (visão 10 anos, registradas mas não implementadas)

| Camada | Quando | Para quê |
|---|---|---|
| **Clinical Graph** | Sprint ≥ 6 | Relações: Patient ↔ Diagnosis ↔ Scales ↔ Meds ↔ Therapies ↔ School ↔ Family ↔ Professionals ↔ Events ↔ Outcomes |
| **Correlation Engine** | Sprint ≥ 6 | Queries tipo "eventos antes de melhora do ATEC" |
| **Research Layer** | Sprint ≥ 6 | ETL → Research Warehouse → Observatório → ML → Publicações |
| **Longitudinal Digital Twin** | Visão 10 anos | Modelo digital contínuo: clínico + funcional + comportamental + terapêutico |

---

## 3. Consequências

### 3.1. Positivas

| Benefício | Como aparece |
|---|---|
| **Single source of truth** | Timeline · Dashboards · IA · Observatório leem `clinical_events` |
| **Auditoria nativa** | Hash chain cobre TODA a história clínica, não apenas audit table |
| **Esquema evolutivo** | Novo `event_type` = linha no catálogo, zero migração Alembic |
| **Replay temporal** | Reconstrução completa: gestação → alta |
| **Observatório desacoplado** | ETL lê do mesmo store, sem duplicação |
| **IA plug-and-play** | Agent consulta `clinical_events`; não importa como módulos produzem |
| **LGPD reforçado** | Soft delete + audit preserva integridade; LGPD purge via `payload` filter |
| **10 anos de evolução** | Schema estável; módulos podem ser reescritos sem perder história |
| **Code reduction** | Estimativa: -20% de código duplicado (dashboards, timelines, reports) |

### 3.2. Custos

| Custo | Mitigação |
|---|---|
| Volume de `clinical_events` cresce indefinidamente | Particionamento por `tenant_id` + `event_datetime` (Sprint 7) |
| Query "tudo do paciente" pode ser lenta | Materialized views + projections (Sprint 5+) |
| Dual-write adiciona latência | Assíncrono em background (Sprint 4); publish síncrono, project assíncrono |
| Curva de aprendizado para o time | ADR + exemplos + primeira sprint com Event Engine sozinho |
| Retrocompatibilidade com `neuro_scale_responses` | Dual-write + consistency check (já planejado) |

### 3.3. Reversibilidade

Decisão **dificilmente reversível** porque:

- Consumidores (dashboards, IA, timeline) passarão a depender do Event Store
- Retrocesso = reescrever todos os consumidores

Mas a decisão é **adiável**: Event Store é adicional, não substitui imediatamente. A coexistência Event Store + Event Bus + tabelas legadas permite rollback tático se a hipótese falhar em produção.

---

## 4. Decisões relacionadas

| Decisão | Status |
|---|---|
| ADR-0001 (este) | ✅ Accepted |
| D1 — `clinical_events` cross-specialty | ✅ Aprovado |
| D2 — Coexistência Event Store + Event Bus | ✅ Aprovado |
| D3 — Dual-write com consistency check diário | ✅ Aprovado |
| D4 — Conditions Catalog global (broader) | ✅ Aprovado |
| D5 — Phenotypes com `source_event_ids` (lista) | ✅ Aprovado |

---

## 5. Plano de implementação

### Sprint 3.1 — Clinical Event Engine (esta sprint)
- `araos/clinical/event_store/` package
- Tabela `clinical_events` (migration Alembic)
- Hash chain SHA-256
- `ClinicalEventPublisher` (dual-write)
- `ClinicalEventStore` (query, replay, verify_integrity)
- Validação contra `_EVENT_CATALOG`
- Consistency check diário
- 95% cobertura

### Sprint 3.2 — Neurodevelopmental Registry
Multi-diagnóstico, status, CID-10/11/DSM-5-TR, profissional, nível de suporte, data. Emite `DIAGNOSIS_*` events.

### Sprint 3.3 — Conditions Catalog (broader)
Catálogo clínico global: diagnósticos, fenótipos, fatores de risco, síndromes, comorbidades, biomarcadores, classificações funcionais. Versionado.

### Sprint 3.4 — Timeline read model
Consome `clinical_events`. História completa: gestação → alta.

### Sprint 3.5 — Longitudinal Phenotypes
12 fenótipos, snapshot materializado, `source_event_ids` lista.

### Sprint 3.6 — Escalas finais
ABC + PSQI + AQ + Conners (12 escalas totais).

### Sprints futuros (4-7) com Event Engine
- Medicações + Cannabis event-sourced
- Dashboards consomem Event Store + projections
- IA lê Event Store; Observatory ETL = 1 query SQL
- Hardening + LGPD + replay test ponta-a-ponta

### Visão 10 anos
- Clinical Graph
- Correlation Engine
- Research Layer + Warehouse
- Longitudinal Digital Twin

---

## 6. Referências

- OpenEHR — Dual Model Architecture
- FHIR R4 — `AuditEvent` resource
- Microsoft — CQRS pattern (azure architecture center)
- Greg Young — Event Sourcing (2010)
- Epic Chronicles — distributed event log (white paper)
- Martin Fowler — Event Sourcing pattern

---

**Esta é a arquitetura de referência para todos os módulos clínicos futuros do AraOS.**

Última atualização: 2026-07-15
