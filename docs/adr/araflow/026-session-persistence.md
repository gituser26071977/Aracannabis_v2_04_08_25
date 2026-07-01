# ADR-026 — Session Persistence

| Field    | Value                                       |
| -------- | REDACTED |
| Status   | Accepted                                    |
| Date     | 2026-06-30                                  |
| Sprint   | 7                                           |
| Author   | AraFlow engineering                         |
| Replaces | (none — first ADR for this domain)          |

---

## Context

Sprint 6 delivered the Session Orchestrator — Runtime ↔ Session bridge.
The Session itself is a pure Aggregate that lives in memory. There is
no way to:

1. save a session for later inspection
2. resume after a process restart
3. detect that a snapshot exists from a previous run
4. migrate snapshots across schema versions

Without a persistence layer, every recovery scenario requires
re-implementing capture + serialize + store + deserialize +
reconstruct per consumer. Sprint 6's Recorder captures SessionEvent
streams in-memory only — usable for replay within a process, not for
persistence across runs.

Sprint 7's brief restricts scope to **local-only persistence** —
no backend, no cloud, no AsyncStorage, no SQLite, no filesystem, no
recovery automation, no UI.

---

## Decision

Create a new module **`@core/session-persistence`** containing a
versioned, deterministic, JSON-serializable snapshot layer:

- a `SessionSerializer` interface (JsonSerializer is the only impl)
- a `StorageAdapter` interface (MemoryStorageAdapter is the only impl)
- a `SessionPersistence` facade that owns both
- a `MigrationRegistry` for cross-version decoding
- a `RecoveryAPI` with explicit `canRecover / recover / discard`
- a `sessionToPersistedSnapshot` projection from ExecutionSession

### Scope

**In scope:**
- Local persistence layer
- Deterministic, lossless JSON serializer with version envelope
- In-memory storage adapter (only one in Sprint 7)
- Migration pathway (registry + decoder interface)
- Explicit Recovery API (no auto-recovery)
- Decoupled from Orchestrator (depends only on ExecutionSession public API)

**Out of scope** (forbidden by brief):
- AsyncStorage / SQLite / IndexedDB / filesystem adapters
- Backend / API / cloud / sync
- UI / React / React Native / Audio / Animation / Analytics / Safety
- Auto-recovery / auto-resume
- Encryption / login / privacy

### Layering

Mirrors the proven pattern from `@core/runtime`,
`@core/execution-session`, and `@core/session-orchestrator`:

```
src/core/session-persistence/
├── index.ts                       — public barrel + SESSION_PERSISTENCE_VERSION
├── domain/                        — interfaces + types (6 files)
├── application/                   — implementations (5 files)
└── util/                          — pure projections (2 files)
```

### Invariants

1. The Orchestrator does not import this module and vice versa.
2. All public methods are async — even MemoryStorageAdapter uses
   resolved Promises.
3. Snapshots are deeply frozen (immutable) on round-trip.
4. `schemaVersion` envelope is mandatory at the wire level.
5. Migrations are explicit (registered) — silent migration is not allowed.
6. Recovery is explicit (consumer-initiated) — no auto-recovery.
7. `RecoveryReason` for failure paths excludes `'recoverable'` and
   `'discarded'` to keep the failure taxonomy narrow.

### Wire Format

```json
{
  "schemaVersion": 1,
  "snapshot": {
    "metadata": { ... },
    "state": "running",
    "metrics": { ... },
    "timeline": [ ... ],
    "events": [ ... ],
    "plan": { ... }
  }
}
```

Sorted keys (deterministic). No precision loss (IEEE-754 doubles).
Branded strings pass through as plain strings.

### Compatibility

- The Orchestrator is frozen at v1.0.0. The persistence layer reads
  only its public read models (`session.events()`, `session.metrics()`,
  `session.timeline()`, `session.plan()`, `session.state()`).
- No engine internals are touched.
- No new dependencies added.

---

## Alternatives Considered

### Alternative A — Add persistence to the Orchestrator

**Rejected.** The Orchestrator is the bridge between Runtime and
Session; adding storage to it conflates two concerns. Persistence
must be downstream and must not modify the Orchestrator contract.

### Alternative B — Use the Session Recorder as the persistence layer

**Rejected.** The Recorder captures SessionEvents only — sufficient
for replay, not for state capture. Persistence needs the full state
snapshot (state + metrics + timeline + events + plan), not just the
event log.

### Alternative C — AsyncStorage from day one

**Rejected.** The brief explicitly defers AsyncStorage / SQLite /
filesystem adapters to future sprints. Sprint 7 ships
`MemoryStorageAdapter` only. The StorageAdapter interface is the seam
that future adapters plug into.

### Alternative D — Auto-recovery on attach

**Rejected.** Auto-recovery conflates persistence with session
lifecycle. Consumers must opt in to recovery (probe → recover →
construct fresh Session). Building a Session from a snapshot is a
Sprint 8 concern.

### Alternative E — Single global SessionPersistence

**Rejected.** PersistenceService is constructed per-Orchestrator (or
per-app) with explicit deps (serializer, storage, migrations). This
allows tests to inject fakes and allows multiple persistence
configurations in a single app.

---

## Consequences

### Positive

- **Decoupled.** Orchestrator and persistence layers are independent
  and meet only at the ExecutionSession public API.
- **Versioned.** `schemaVersion` + `MigrationRegistry` allow safe
  schema evolution.
- **Deterministic.** Sorted-key JSON enables byte-stable snapshots
  (useful for change detection, hashing, deduplication).
- **Lossless.** Numbers preserve IEEE-754 doubles; no precision loss.
- **Explicit recovery.** No auto-recovery — consumer-driven.
- **Pluggable storage.** `StorageAdapter` is the seam for future
  AsyncStorage / SQLite / IndexedDB / filesystem adapters.
- **Result-free errors.** All failures are typed — `SaveFailureReason`
  and `LoadFailureReason` are exhaustive unions.

### Negative

- **No real persistence in Sprint 7.** MemoryStorageAdapter loses
  data on process restart. Future sprint adds the real backend.
- **No auto-recovery.** Consumers must wire recovery themselves.
- **Coverage ~96%.** Branches at 90% reflect a few defensive error
  paths in PersistenceService; per-path threshold is configured
  (90/80/90/90) and met.

### Compliance

- ✅ Sprint 7 brief — interfaces, serializers, versionamento, storage
  abstraction, recovery API, no persistence backend, no UI, no Audio,
  no Analytics, no Safety.
- ✅ `@araflow/32_FINAL_PRODUCT_DECISIONS.md` — clean architecture,
  pure domain, no UI.
- ✅ `@araflow/33_ENGINEERING_BLUEPRINT.md` — layered architecture
  (domain / application / util), barrel exports, Result-based API.
- ✅ Frozen engines — Orchestrator + ExecutionSession at v1.0.0
  unchanged.

---

## Implementation notes

- All mutable state lives on the application layer (services,
  adapters). Domain types and util functions are pure.
- `Object.freeze` is applied to all parsed payloads (snapshots,
  events, plans).
- The `deterministic-json` util is the only place that knows the
  wire format. Future serializers (e.g. MessagePack, Protobuf) plug
  in via the `SessionSerializer` interface.
- 94 unit tests covering: serializer round-trip, deterministic JSON,
  storage CRUD, save/load/delete/exists/list/clear, corruption,
  incompatibility, migrations, recovery API, session-to-snapshot
  projection, type guards.

## Sprint 7 acceptance criteria (answered)

1. **Orchestrator decoupled?** — Yes. Persistence depends only on
   `@core/execution-session`'s public API; Orchestrator has zero
   imports from this module.
2. **MemoryStorage → AsyncStorage without changing rules?** — Yes.
   Swap the `StorageAdapter` dep; PersistenceService contract is
   unchanged.
3. **Format supports migrations?** — Yes. `schemaVersion` envelope
   + `MigrationRegistry` map versions to decoders.
4. **Data loss on serialization?** — No. Deterministic JSON, no
   BigInt, no Date, no truncation.
5. **Recovery ready for Sprint 8?** — Yes. `canRecover / recover /
   discard` exposed; building a fresh Session from a snapshot is the
   Sprint 8 task.
6. **Coverage ≥90/80/90/90?** — Yes. Aggregate: 96/90/100/96.
7. **External dependencies added?** — No.
8. **Ready for integration?** — Yes. PersistenceService +
   RecoveryAPI + InMemoryStorage are wired and tested.