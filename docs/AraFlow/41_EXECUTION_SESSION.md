# AraFlow — Execution Session Domain

> **The single source of truth of a breathing session.**

Version: 1.0.0 (Sprint 5)
Location: `mobile/src/core/execution-session/`
Public API: `@core/execution-session`

---

## 1. Mission

The Execution Session is a **Domain-Driven Design Aggregate Root** that
represents a single breathing session in execution. It is the canonical
model that downstream layers (UI, Audio, Animation, Session Engine)
consume. The Session owns its identity, its frozen execution plan, its
finite state machine, its event log, and its derived read models
(metrics, timeline, snapshot).

The Session is **pure domain**. It has no dependencies on persistence,
network, UI, React, React Native, Audio, Animation, Analytics, or Safety.

---

## 2. Architecture

```
mobile/src/core/execution-session/
├── index.ts                                    — public barrel
├── domain/                                     — pure domain types
│   ├── SessionState.ts                         — 8-state FSM + transitions
│   ├── SessionEvent.ts                         — tagged-union event log
│   ├── SessionMetrics.ts                       — derived numeric read model
│   ├── SessionSnapshot.ts                      — immutable point-in-time view
│   └── SessionTimeline.ts                      — UI-independent session beats
├── application/                                — Aggregate Root + plumbing
│   ├── ExecutionSession.ts                     — main aggregate (API)
│   ├── ExecutionSessionDeps.ts                 — constructor options
│   └── SessionEventLog.ts                      — append-only event log
└── util/                                       — pure projections
    ├── session-metrics.ts                      — events → SessionMetrics
    └── session-timeline.ts                     — events → SessionTimeline
```

The layering is identical to `@core/runtime`:

| Layer          | Responsibility                                            |
| -------------- | REDACTED |
| `domain/`      | Pure types, FSM, tagged unions. No behavior.              |
| `application/` | Aggregate Root, event log, lifecycle methods.             |
| `util/`        | Pure projections from events to read models.              |

---

## 3. Aggregate Root Invariants

The `ExecutionSession` class enforces five hard invariants:

1. **Identity immutability** — `sessionId`, `protocolId`, `executionPlanId`
   never change after construction.
2. **Plan reference immutability** — the injected `ProtocolExecutionPlan`
   is held by reference and never replaced or mutated.
3. **Event log append-only** — past events are `Object.freeze`d and never
   mutated. Every append produces a new frozen array.
4. **FSM transitions** — every state transition is validated against the
   `legalTransitions` table. Illegal transitions return `Err`.
5. **Snapshot version monotonicity** — `snapshot.version` increments on
   every state change. Snapshots are immutable.

These invariants are checked by the `ExecutionSession` constructor and
every public method. Tests in `ExecutionSession.test.ts` cover each one.

---

## 4. State Machine (8 states)

```
                ┌───────┐
                │ idle  │
                └───┬───┘
                    │ start()
                    ▼
              ┌───────────┐
              │ preparing │
              └─────┬─────┘
                    │ (auto)
                    ▼
        ┌───────────────────┐
        │      running      │ ◄──────┐
        └──┬──────┬──────┬──┘        │ resume()
           │      │      │           │
   pause() │      │      │           │
           ▼      │      │           │
        ┌──────┐  │      │           │
        │paused│──┘      │           │
        └──┬───┘         │           │
           │             │           │
           │   ┌─────────┴─────────┐ │
           │   ▼                   ▼ │
           │ ┌────────┐      ┌────────────┐
           │ │complete│      │ cancelled  │
           │ └────────┘      └────────────┘
           │   ┌────────────┐  ┌────────────┐
           │   │ interrupted│  │  failed    │
           │   └────────────┘  └────────────┘
           │
           └──► (cancel/complete/fail/interrupt from any non-terminal)
```

**States:**
- `idle` — initial state, plan loaded but session not started.
- `preparing` — transient state during `start()`.
- `running` — session in execution.
- `paused` — session temporarily halted (timer stopped).
- `completed` — terminal: session finished naturally.
- `cancelled` — terminal: user/system cancelled.
- `interrupted` — terminal: external interruption (OS, network).
- `failed` — terminal: unrecoverable error.

**Terminal states** (`completed`, `cancelled`, `interrupted`, `failed`)
have no outgoing transitions. Disposal is orthogonal — `dispose()` is
always allowed.

The transition table is exposed via `legalTransitions(state)`. Adding
a new state requires updating this table.

---

## 5. Event Sourcing (in-memory)

Every state change emits a domain event. Events are immutable
(`Object.freeze`). The session's event log is the canonical audit trail.

**Lifecycle events:**
- `session-created`
- `session-preparing`
- `session-started`
- `session-paused`
- `session-resumed`
- `session-cancelled`
- `session-completed`
- `session-failed`
- `session-interrupted`

**Observation events:**
- `phase-changed`
- `cycle-completed`
- `metric-updated`
- `snapshot-created`

Each event carries `monotonicMs` for deterministic ordering.
Downstream projections (metrics, timeline) derive their state from
this log.

The session state can be reconstructed from a log replay alone. The
log is in-memory only (no persistence).

---

## 6. Snapshot

`session.snapshot()` returns an immutable `SessionSnapshot` containing:

| Field            | Type                  | Source                              |
| ---------------- | --------------------- | REDACTED |
| `sessionId`      | `SessionId`           | Constructor (invariant)             |
| `protocolId`     | `ProtocolId`          | Constructor (invariant)             |
| `executionPlanId`| `ExecutionPlanId`     | Constructor (invariant)             |
| `state`          | `SessionState`        | FSM                                 |
| `elapsedMs`      | `number`              | `metrics.elapsedMs`                 |
| `remainingMs`    | `number`              | `metrics.remainingMs`               |
| `currentPhase`   | `BreathPhase \| null` | Last `phase-changed` event          |
| `currentCycle`   | `number`              | Last `phase-changed` / cycle counter|
| `progress`       | `number` (0..1)       | `elapsedMs / plannedDurationMs`      |
| `metrics`        | `SessionMetrics`      | Full derived read model             |
| `timestamp`      | `number`              | Current `now()` call                |
| `version`        | `number`              | Incremented on each state change    |

Calling `snapshot()` emits a `snapshot-created` event so the log
reflects the observation. Snapshots are frozen and may be safely
passed across boundaries.

---

## 7. Timeline

`session.timeline()` returns a `SessionTimeline` — an ordered list of
UI-independent session beats. Each entry has:

```ts
{
  monotonicMs: number;        // start time
  durationMs: number;         // duration in this beat
  kind: SessionTimelineKind;  // 'prepare' | 'inhale' | 'exhale' | 'hold' |
                              // 'cycle' | 'pause' | 'resume' | 'complete' |
                              // 'cancel' | 'fail' | 'interrupt'
  phase?: BreathPhase;
  cycleIndex?: number;
  phaseIndex?: number;
}
```

The timeline is pure projection from the event log. The UI layer is
free to render it as "00:00 Inhale, 00:15 Exhale, ..." without the
domain knowing anything about formatting.

Consecutive same-kind phase entries (`inhale`/`exhale`/`hold`) are
merged into a single entry to keep the timeline compact.

---

## 8. Metrics

`session.metrics()` returns a `SessionMetrics` with:

| Field             | Description                                       |
| ----------------- | REDACTED |
| `elapsedMs`       | Total ms of active (non-paused) execution         |
| `remainingMs`     | `plannedDurationMs - elapsedMs` (clamped to 0)    |
| `completedCycles` | Number of `cycle-completed` events emitted        |
| `currentCycle`    | `max(currentCycle, completedCycles)`              |
| `currentPhase`    | Phase from most recent `phase-changed` event      |
| `progress`        | `elapsedMs / plannedDurationMs`, clamped to [0,1] |
| `pauseCount`      | Number of pause/resume cycles                     |
| `pauseDurationMs` | Total ms spent in paused state                    |
| `sessionDurationMs` | wall-clock duration from start to end/now       |

Metrics are derived purely from the event log. They are computed
lazily on each `metrics()` call (no caching).

---

## 9. Public API

```ts
import {
  ExecutionSession,
  ExecutionPlanId,
  // ... types
} from '@core/execution-session';

const session = new ExecutionSession({
  sessionId: SessionId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  protocolId: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  executionPlanId: ExecutionPlanId('01HXYZ00000000000000000000'),
  plan: compiledPlan,
  now: () => Date.now(),  // optional; defaults to Date.now
});

// Lifecycle
session.start();
session.pause();
session.resume();
session.cancel('user_requested');
session.complete();
session.fail('engine_error', 'something went wrong');
session.interrupt('os_pause');

// Observation (drives derived metrics)
session.recordPhaseChange({ phase: 'inhaling', cycleIndex: 0, phaseIndex: 0, phaseElapsedMs: 0, phaseDurationMs: 4000 });
session.recordCycleCompleted({ cycleIndex: 0, cycleElapsedMs: 8000, totalCycles: 4 });

// Read models
session.state();        // 'idle' | 'preparing' | 'running' | 'paused' | ...
session.snapshot();     // SessionSnapshot (frozen)
session.metrics();      // SessionMetrics
session.timeline();     // SessionTimeline
session.events();       // readonly SessionEvent[]

// Identity (invariants)
session.sessionId();
session.protocolId();
session.executionPlanId();
session.plan();

// Lifecycle cleanup
session.dispose();
```

All lifecycle methods return `Result<void, EngineError>`. Use
`isOk()` / `isErr()` to branch on the outcome.

---

## 10. Lifecycle Invariants in Practice

1. **Identity** — `sessionId()`, `protocolId()`, `executionPlanId()`
   return the same value across the session's lifetime.
2. **Plan** — `plan()` returns the same `ProtocolExecutionPlan`
   reference passed to the constructor.
3. **Event log** — past events never change. New events only append.
4. **State transitions** — `start()` from `idle` is allowed; from
   `completed` returns `Err`. `cancel()` from terminal is a no-op
   (`Ok`). `pause()` from `running` is allowed; from `idle` returns
   `Err`.
5. **Version** — `snapshot().version` strictly increases with state
   changes.

---

## 11. Compatibility with `@core/runtime`

The Runtime (Sprint 4) and the Session (Sprint 5) are **complementary
but independent** domain models:

| Concern                | Runtime             | Session             |
| ---------------------- | ------------------- | ------------------- |
| State count            | 10 (engine-focused) | 8 (user-focused)    |
| Owns engines?          | Yes (3 engines)     | No (pure domain)    |
| External events?       | Yes (subscribes)    | No (driven by API)  |
| Persistence?           | No                  | No                  |
| Audience               | Engine integrators  | UI/Session Engine   |

A future Session Engine (out of scope for Sprint 5) will bridge the
two: consume Runtime events and feed them to the Session via
`recordPhaseChange` / `recordCycleCompleted`.

---

## 12. References

- `40_RUNTIME.md` — AraFlow Runtime (Sprint 4)
- `40_SPRINT4_RUNTIME_REPORT.md` — Runtime sprint report
- ADR-023 — Runtime Facade
- ADR-024 — Execution Session Domain
- `REDACTED.md` — This sprint's report