# AraFlow — Session Persistence

> **Local-only persistence for the AraFlow Session Orchestrator.**

Version: 1.0.0 (Sprint 7)
Location: `mobile/src/core/session-persistence/`
Public API: `@core/session-persistence`

---

## 1. Mission

The Session Persistence layer captures a Session's full state into a
versioned, JSON-serializable **PersistedSessionSnapshot**, stores it
through an abstract **StorageAdapter**, and exposes an explicit
**Recovery API**. The Orchestrator remains unchanged: persistence is
downstream and depends on the Orchestrator's public read models, never
on internals.

The layer is **local-only**. No backend, no cloud, no AsyncStorage,
no SQLite, no filesystem, no UI, no Audio, no Analytics, no Safety.
The only StorageAdapter in scope is `MemoryStorageAdapter`; future
sprints introduce AsyncStorage / SQLite adapters without changing
the public API.

---

## 2. Architecture

```
mobile/src/core/session-persistence/
├── index.ts                                    — public barrel + SESSION_PERSISTENCE_VERSION
├── domain/                                     — interfaces and pure types
│   ├── SnapshotMetadata.ts                     — header (id, timestamps, version)
│   ├── SessionSnapshot.ts                      — PersistedSessionSnapshot + StorageRecord
│   ├── StorageAdapter.ts                       — abstract storage seam
│   ├── SessionSerializer.ts                    — encode/decode seam
│   ├── SessionPersistence.ts                   — high-level seam
│   └── RecoveryDecision.ts                     — probe + result types
├── application/                                — implementations
│   ├── JsonSerializer.ts                       — deterministic JSON encoder
│   ├── MemoryStorageAdapter.ts                 — in-memory storage (only impl in scope)
│   ├── PersistenceService.ts                   — wires serializer + storage + migrations
│   ├── MigrationRegistry.ts                    — version → decoder map
│   └── RecoveryAPI.ts                          — canRecover / recover / discard
└── util/
    ├── deterministic-json.ts                   — sorted-keys JSON stringify
    └── session-to-snapshot.ts                  — pure: ExecutionSession → PersistedSnapshot
```

| Layer          | Responsibility                                                   |
| -------------- | REDACTED |
| `domain/`      | Pure types, seams, factories. No behavior.                       |
| `application/` | Adapters, services, registries.                                  |
| `util/`        | Pure projections from ExecutionSession → PersistedSessionSnapshot. |

---

## 3. Responsibilities

The Persistence layer:

1. **Captures** a Session's full state (state, metrics, timeline,
   events, plan) into a `PersistedSessionSnapshot` via
   `sessionToPersistedSnapshot`.
2. **Serializes** deterministically with `JsonSerializer` (sorted
   keys, version envelope).
3. **Persists** through any `StorageAdapter` (in-memory in Sprint 7).
4. **Deserializes** on load, validating schema version and routing to
   migrations when needed.
5. **Exposes** an explicit `RecoveryAPI` (canRecover / recover /
   discard). **No auto-recovery.**
6. **Supports cross-version migration** via `MigrationRegistry`.

---

## 4. Public API

```ts
import {
  createJsonSerializer,
  createMemoryStorageAdapter,
  createPersistenceService,
  createMigrationRegistry,
  createRecoveryAPI,
  sessionToPersistedSnapshot,
  stringifyDeterministic,
  parseDeterministic,
  // ... types
} from '@core/session-persistence';

// Wire it up
const serializer = createJsonSerializer();
const storage = createMemoryStorageAdapter();
const migrations = createMigrationRegistry();
const persistence = createPersistenceService({ serializer, storage, migrations });
const recovery = createRecoveryAPI({ persistence });

// Save
const snap = sessionToPersistedSnapshot({
  session,
  capturedAtMonotonicMs: Date.now(),
  serializerVersion: 1,
});
await persistence.save({ sessionId: session.sessionId(), snapshot: snap });

// Probe + recover
const probe = await recovery.canRecover(sessionId);
if (probe.canRecover) {
  const result = await recovery.recover(sessionId);
  // result.snapshot is the full PersistedSessionSnapshot
}

// Discard
await recovery.discard(sessionId);
```

---

## 5. Snapshot Shape

```ts
interface PersistedSessionSnapshot {
  readonly metadata: SnapshotMetadata;     // identity + timestamps + version
  readonly state: SessionState;
  readonly metrics: SessionMetrics;
  readonly timeline: SessionTimeline;
  readonly events: readonly SessionEvent[];
  readonly plan: ProtocolExecutionPlan;
}

interface SnapshotMetadata {
  readonly snapshotId: string;
  readonly sessionId: SessionId;
  readonly protocolId: ProtocolId;
  readonly executionPlanId: ExecutionPlanId;
  readonly stage: 'in-flight' | 'terminal';
  readonly capturedAtMonotonicMs: number;
  readonly updatedAtMonotonicMs: number;
  readonly serializerVersion: number;
  readonly label?: string;
}
```

All fields are required (label is optional). Snapshots are
immutable (deeply frozen) on round-trip through the serializer.

---

## 6. Wire Format (schemaVersion 1)

```
{
  "schemaVersion": 1,
  "snapshot": { ... PersistedSessionSnapshot ... }
}
```

- Sorted keys (deterministic).
- Branded strings (SessionId, ProtocolId, ExecutionPlanId) pass
  through as plain strings (they're strings at runtime).
- Numbers preserved as IEEE-754 doubles (no precision loss).
- No `Date` instances; consumers pass `monotonicMs` numbers.

---

## 7. StorageAdapter

`StorageAdapter` is the seam between persistence and storage
backend. The interface stores opaque strings keyed by sessionId. It
does NOT interpret the payload.

```ts
interface StorageAdapter {
  readonly adapterId: string;
  write(key: string, payload: string, options?: { overwrite?: boolean }): Promise<void>;
  read(key: string): Promise<{ payload: string | null; updatedAtMonotonicMs: number }>;
  delete(key: string): Promise<void>;
  exists(key: string): Promise<boolean>;
  list(): Promise<readonly string[]>;
  clear(): Promise<void>;
}
```

`MemoryStorageAdapter` (only impl in Sprint 7) is a thin Map wrapper
with optional monotonic clock injection for tests.

**AsyncStorage, SQLite, IndexedDB, filesystem adapters are out of
scope for Sprint 7.** Future sprints introduce them without changing
the public API.

---

## 8. SessionPersistence

The high-level facade. Saves a snapshot under a sessionId; loads it
back. Errors are typed:

```ts
type SaveFailureReason = 'no-snapshot' | 'serialize-failed' | 'storage-failed';
type LoadFailureReason = 'not-found' | 'corrupted' | 'incompatible' | 'storage-failed';
```

`incompatible` is returned when the stored `schemaVersion` doesn't
match the current serializer AND no migration is registered.

---

## 9. Migrations

```ts
const migrations = createMigrationRegistry().register(0, {
  schemaVersion: 0,
  decode: (encoded: string) => {
    // parse + transform v0 → v1 shape
    return v1Snapshot;
  },
});
```

The PersistenceService on `load` checks the stored `schemaVersion`:

- matches current → decode via the active serializer
- matches a registered legacy version → decode via the registered decoder
- otherwise → return `incompatible`

---

## 10. Recovery API

Per Sprint 7 brief: **no auto-recovery**. Consumers explicitly:

1. **Probe** — `canRecover(sessionId) → RecoveryProbe`
   - `canRecover: boolean`
   - `reason: 'recoverable' | 'no-snapshot' | 'corrupted' | 'incompatible' | 'discarded'`
   - `snapshotVersion: number | null`
2. **Recover** — `recover(sessionId) → RecoveryResult`
   - `ok: true` with the snapshot, OR
   - `ok: false` with a `RecoveryReason` (no `recoverable`/`discarded` in the failure branch)
3. **Discard** — `discard(sessionId) → void` (removes the snapshot)

Building a fresh ExecutionSession from a recovered snapshot is a
Sprint 8 concern (the brief defers it).

---

## 11. Decoupling from Orchestrator

The Persistence layer depends on:
- `@core/execution-session` (public read models only)
- `@core/protocol-compiler` (ProtocolExecutionPlan type)
- `@araflow/shared-contracts` (branded id types)

It does NOT import anything from `@core/session-orchestrator` and
does NOT modify the Orchestrator. The Orchestrator does not import
this module. The two modules are independent and only share the
ExecutionSession as a contract.

To swap MemoryStorageAdapter for AsyncStorage:

```ts
const storage: StorageAdapter = createAsyncStorageAdapter({ ... });
const persistence = createPersistenceService({ serializer, storage });
```

No other code changes.

---

## 12. References

- `@core/execution-session` — Aggregate Root (Sprint 5)
- `@core/session-orchestrator` — Bridge (Sprint 6)
- `@core/protocol-compiler` — Plan type
- `REDACTED.md` — Sprint 7 report
- ADR-026 — Session Persistence