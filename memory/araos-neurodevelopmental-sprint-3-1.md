---
name: REDACTED
description: AraOS NEURODEVELOPMENTAL Sprint 3.1 — Clinical Event Engine (foundation) entregue; 239 testes / 99% cobertura; sequence per-tenant para chain canônica; ADR-0001 atualizado
metadata:
  type: project
---

Sprint 3.1 do Módulo NEURODESENVOLVIMENTO entregou o **Clinical Event Engine** (ADR-0001), fundação arquitetural cross-specialty.

## Entregue
- Pacote `araos.clinical.event_store` (7 módulos, ~620 LOC backend, ~1.350 LOC testes)
- Tabela `clinical_events` + tabela `clinical_event_sequences` (per-tenant tracker)
- Migração Alembic `2026_07_15_cee_s31`
- 26 event types catalogados (cross-specialty: Neuro, Cannabis, Fisio, Fono, TO, Psicologia, Psiquiatria, UTI, Dor, Sono, Reabilitação)
- `ClinicalEventPublisher` (valida catálogo + schema, escreve no store, fan-out para bus com graceful degradation)
- `InMemoryClinicalEventStore` (thread-safe via RLock) + `SqlAlchemyClinicalEventStore` (PostgreSQL/SQLite)
- SHA-256 hash chain com canonical JSON
- Atomic per-tenant sequence allocation (`SELECT ... FOR UPDATE` em PG, serialização natural em SQLite)
- Wildcard query (`event_types=["DIAGNOSIS_*"]`)

## Métricas
- **239 testes (100% passing)**
- **99% cobertura** (target ≥95%)
- 26 event types no catalog

## Decisão arquitetural chave: sequence per-tenant
Ordenação canônica da chain é por **sequence (insertion order)**, não por `event_datetime` (clinical time).
- `event_datetime` é atributo do payload (pode ser backdated, batch-imported, registrado com delay)
- `sequence` é a verdade imutável de "quando o sistema tomou conhecimento"
- Permite UNIQUE constraint `(tenant_id, sequence)` → integridade adicional
- Migration atualizada: `ix_clinical_events_tenant_sequence` + `uq_clinical_events_tenant_sequence`
- Schema timezone preservado em to_dict via `_isoformat_utc()` (SQLite strippa tzinfo no round-trip)

## ADR atualizado
`docs/adr/0001-clinical-event-engine.md` ganhou seção 2.3.1 documentando a decisão `sequence`.

## Próxima sprint (3.2)
Neurodevelopmental Registry — adapter que dual-writes eventos Neuro no Event Store. Tabela legada continua, novos eventos vão para `clinical_events`. Consistency check diário.

**Why:** Foundation arquitetural para todos os módulos clínicos futuros. Reference architecture AraOS.
**How to apply:** Usar `ClinicalEventPublisher.publish(...)` em qualquer módulo que precise emitir evento clínico. Nunca escrever direto em read model. Novo event_type = 1 entrada no `CLINICAL_EVENT_CATALOG`.

Relacionado: [[araos-clinical-event-engine-adr]] [[araos-neurodevelopmental-sprint-3]]