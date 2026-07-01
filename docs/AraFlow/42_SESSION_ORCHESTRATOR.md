# AraFlow — Session Orchestrator

> **The bridge between Runtime and Execution Session.**

Version: 1.0.0 (Sprint 6)
Location: `mobile/src/core/session-orchestrator/`
Public API: `@core/session-orchestrator`

---

## 1. Mission

The Session Orchestrator is the **bridge** between the AraFlow Runtime
(engine-level) and the Execution Session (user-level). It consumes
Runtime events, translates them into Session API calls, detects
inconsistencies, supports replay, and integrates with an in-memory
Recorder.

The Orchestrator is **pure domain logic** with an internal event stream.
It has no dependencies on persistence, network, UI, React, React Native,
Audio, Animation, Analytics, or Safety.

---

## 2. Architecture

```
mobile/src/core/session-orchestrator/
├── index.ts                                    — public barrel + SESSION_ORCHESTRATOR_VERSION
├── domain/                                     — pure domain types
│   ├── OrchestratorState.ts                    — 4-state FSM
│   ├── OrchestratorEvent.ts                    — tagged-union of Orchestrator events
│   ├── InconsistencyReport.ts                  — typed inconsistencies (5 kinds)
│   ├── SessionRecording.ts                     — JSON-serializable recording
│   └── OrchestratorMetrics.ts                  — derived counters
├── application/                                — bridge + plumbing
│   ├── SessionOrchestrator.ts                  — main class (the bridge)
│   ├── SessionOrchestratorDeps.ts              — constructor options
│   ├── OrchestratorEventStream.ts              — tagged-union dispatcher
│   └── SessionRecorder.ts                      — in-memory recorder
└── util/                                       — pure projections
    ├── event-translator.ts                     — RuntimeEvent → SessionAction
    ├── consistency-checks.ts                   — detects 5 kinds of inconsistencies
    ├── replay-reducer.ts                       — events → Session state reconstruction
    └── recording-format.ts                     — Recording ⇄ JSON
```

| Layer          | Responsibility                                            |
| -------------- | REDACTED |
| `domain/`      | Pure types, FSM, tagged unions, factories. No behavior.   |
| `application/` | Bridge class, recorder, event stream.                     |
| `util/`        | Pure projections from Runtime events to Session actions. |

---

## 3. Aggregate Bridge Responsibilities

The Orchestrator:

1. **Connects** Runtime and Execution Session via `attach()`.
2. **Consumes** Runtime events by subscribing to the unified stream.
3. **Updates** the Session by translating each Runtime event into a
   typed SessionAction and invoking the appropriate Session API call.
4. **Detects inconsistencies** in 5 categories (out-of-order,
   impossible-state, invalid cycle, invalid phase, divergence).
5. **Publishes consolidated state** through its own OrchestratorEvent
   stream — separate from the Runtime stream.
6. **Supports replay** of a recorded SessionRecording to reconstruct a
   Session deterministically.
7. **Integrates with Recorder** for in-memory capture of every Session
   event emitted during bridge operation.

---

## 4. Event Mapping (Runtime → Session)

| Runtime event                                | Session API call                  |
| REDACTED | --------------------------------- |
| `protocol-runtime-started`                   | `session.start()`                 |
| `protocol-runtime-paused`                    | `session.pause()`                 |
| `protocol-runtime-resumed`                   | `session.resume()`                |
| `protocol-runtime-phase-changed`             | `session.recordPhaseChange(...)`  |
| `protocol-runtime-cycle-completed`           | `session.recordCycleCompleted()`  |
| `protocol-runtime-completed`                 | `session.complete()`              |
| `protocol-runtime-stopped` (cancelled)       | `session.cancel()`                |
| `protocol-runtime-stopped` (errored)         | `session.fail(...)`               |
| `protocol-runtime-errored`                   | `session.fail(...)`               |
| `protocol-runtime-tick`                      | skip (high-frequency)             |
| `timer-*` / `breath-*`                       | skip (engine-level noise)         |
| `runtime-compile-failed`                     | skip (no Session to fail)         |
| `runtime-error`                              | `session.fail(...)`               |
| `runtime-warnings`                           | skip                              |
| `runtime-completed`                          | `session.complete()`              |
| `runtime-disposed`                           | `session.dispose()`               |

The mapping is implemented in `util/event-translator.ts` as a pure
function `translateRuntimeEvent(event: RuntimeEvent): SessionAction`.

---

## 5. Consistency Checks

The Orchestrator runs five categories of checks before each translation:

1. **out-of-order** — Runtime event timestamp is older than the last
   event the Orchestrator has seen.
2. **impossible-state** — Runtime event requires a Session state that
   cannot legally receive it (e.g. `pause` when Session is idle).
3. **invalid-cycle** — `cycle-completed` cycleIndex ≥ plan.cycles.
4. **invalid-phase** — `phase-changed` references a phase outside plan.
5. **divergence** — Runtime and Session states are incompatible.

Each report is a frozen `InconsistencyReport` with a typed
`InconsistencyKind`. Reports are appended (never mutated) and exposed
via `orchestrator.inconsistencies()`.

Implementation: `util/consistency-checks.ts` (pure function
`runConsistencyChecks(input): readonly InconsistencyReport[]`).

---

## 6. State Machine

The Orchestrator has its own 4-state FSM:

```
                ┌──────────┐
                │ detached │
                └────┬─────┘
            attach()  │  detach()
                     ▼
                ┌──────────┐
                │ attached │
                └────┬─────┘
                     │ replay()
                     ▼
                ┌──────────┐
                │replaying │
                └────┬─────┘
                     │
                     ▼
                (back to attached or detached)

any ─────► disposed (terminal)
```

`dispose()` is orthogonal — allowed from any non-terminal state.

---

## 7. Public API

```ts
import {
  SessionOrchestrator,
  SessionRecorder,
  // ... types
} from '@core/session-orchestrator';

const orchestrator = new SessionOrchestrator({
  runtime,             // RuntimeEngine instance
  session,             // ExecutionSession instance
  onListenerError?,    // optional sink for listener exceptions
  now?,                // optional monotonic clock
});

// Bridge
orchestrator.attach();    // subscribe to Runtime
orchestrator.detach();    // unsubscribe

// Replay
orchestrator.replay(recording.events);                   // into existing session
orchestrator.replay(recording.events, plan);             // reconstruct fresh session
SessionOrchestrator.replayIntoSession({ recording, plan }); // static helper

// Recorder integration
const recorder = new SessionRecorder({ sessionId, protocolId, executionPlanId });
orchestrator.attachRecorder(recorder);
recorder.export(1000);     // → SessionRecording
SessionRecorder.import(recording); // → new SessionRecorder

// Read models
orchestrator.state();              // OrchestratorState
orchestrator.runtimeState();       // RuntimeState
orchestrator.sessionState();       // SessionState
orchestrator.sessionSnapshot();    // SessionSnapshot
orchestrator.inconsistencies();    // readonly InconsistencyReport[]
orchestrator.metrics();            // OrchestratorMetrics
orchestrator.sessionId();
orchestrator.protocolId();

// Subscribe to Orchestrator events
orchestrator.subscribe((event) => { ... });

// Cleanup
orchestrator.dispose();
```

---

## 8. Replay

Replay reconstructs a Session from a recorded event log:

- `orchestrator.replay(events)` — drives the existing session through
  the events; identity must match.
- `orchestrator.replay(events, plan)` — constructs a fresh
  `ExecutionSession` from the anchor event's identity + the provided
  plan; replay is deterministic.
- `SessionOrchestrator.replayIntoSession({ recording, plan })` —
  static helper that always constructs a fresh session.

Replay emits `orchestrator-replayed` on success. Errors are returned as
`Result<ExecutionSession, EngineError>`.

Replay is **deterministic**: same recording + plan → same resulting
Session state (modulo wall-clock timestamps).

---

## 9. Recorder

The Recorder is in-memory. It captures every Session event emitted
during bridge operation (via `recordMany` after each action).

```ts
const recorder = new SessionRecorder({ sessionId, protocolId, executionPlanId });

// Capture happens automatically when attached to an Orchestrator.
orchestrator.attachRecorder(recorder);

// Or manually:
recorder.record(event);
recorder.recordMany(events);

// Export:
const recording = recorder.export(monotonicMs);   // SessionRecording
const json = recorder.exportJson(monotonicMs);   // JSON-safe

// Import:
const r2 = SessionRecorder.import(recording);
const r3 = SessionRecorder.importJson(json);
```

The `SessionRecording` shape is JSON-serializable and version-tagged
(`version: 1`). Future persistence layers can serialize the JSON
directly.

---

## 10. Inconsistency Reports

```ts
type InconsistencyKind =
  | 'out-of-order'
  | 'impossible-state'
  | 'invalid-cycle'
  | 'invalid-phase'
  | 'divergence';
```

Each `InconsistencyReport` is a frozen object:

```ts
interface InconsistencyReport {
  kind: InconsistencyKind;
  code: string;          // e.g. 'orchestrator_impossible_state'
  message: string;
  monotonicMs: number;
  context: Readonly<Record<string, unknown>>;
}
```

Reports are exposed via `orchestrator.inconsistencies()` and counted
in `orchestrator.metrics().inconsistencies`. Each detection also emits
an `orchestrator-inconsistency` event for subscribers.

---

## 11. Compatibility with Runtime & Session

The Orchestrator depends on:

- `@core/runtime` — RuntimeEngine (read-only: subscribe + getState).
- `@core/execution-session` — ExecutionSession (driven by orchestrator
  API calls).

It does NOT consume Runtime events from any other source. It does NOT
expose Runtime events directly (consumers subscribe to Runtime for
that). It only emits Orchestrator-specific events.

---

## 12. References

- `@core/runtime` — Runtime Facade (Sprint 4)
- `@core/execution-session` — Execution Session (Sprint 5)
- `REDACTED.md` — Sprint 6 report
- ADR-025 — Session Orchestrator