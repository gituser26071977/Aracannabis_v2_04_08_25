# ADR-024 — Execution Session Domain

| Field    | Value                                      |
| -------- | REDACTED |
| Status   | Accepted                                   |
| Date     | 2026-06-29                                 |
| Sprint   | 5                                          |
| Author   | AraFlow engineering                        |
| Replaces | (none — first ADR for this domain)         |

---

## Context

Sprint 4 (AraFlow Runtime) delivered the **engine-level API** for the
AraFlow Core. The Runtime wraps three engines (Timer, Breath,
Protocol) behind a 12-method API and a tagged-union event stream.

However, the Runtime's state machine (10 states) is engine-oriented.
It lacks concepts the user-facing layer cares about:

- **Pre-flight state** (idle, preparing) — the Runtime starts at
  `'uninitialized'` and jumps straight to `'loaded'` via `loadProtocol`.
- **Interruption** — Runtime treats any non-success termination as
  `'errored'`. There is no distinction between "user cancelled",
  "external interruption" (OS pause), and "engine failure".
- **Progress / completion** — the Runtime doesn't carry a "this
  session is 60% complete" view. UI layers would have to derive it.
- **Snapshot of a single session** — Runtime snapshots cover the
  engine state at one moment; there's no concept of "this user's
  current session" as a first-class object.

Without an Execution Session model, every consumer (UI, Audio
Engine, Session Engine, Analytics) would re-implement the same
projection logic on top of Runtime events. The exploration phase
surfaced 5 distinct gaps that this duplication would cause.

---

## Decision

Create a new module **`@core/execution-session`** containing a
**DDD Aggregate Root** — `ExecutionSession` — that is the single
source of truth of a breathing session in execution.

### Scope

**In scope:**
- Identity (`SessionId`, `ProtocolId`, `ExecutionPlanId`)
- Frozen `ProtocolExecutionPlan` reference
- 8-state FSM (`idle`, `preparing`, `running`, `paused`,
  `completed`, `cancelled`, `interrupted`, `failed`)
- Append-only immutable event log
- Read models: `SessionMetrics`, `SessionSnapshot`, `SessionTimeline`
- Lifecycle API: `start`, `pause`, `resume`, `cancel`, `complete`,
  `fail`, `interrupt`, `dispose`
- Observation API: `recordPhaseChange`, `recordCycleCompleted`
- Read API: `snapshot`, `metrics`, `timeline`, `events`, `state`

**Out of scope** (forbidden by brief):
- Persistence (no DB, no storage)
- Network (no API clients, no HTTP)
- UI (no React, no React Native, no `@mui`)
- Audio (no sound, no synthesis, no playback)
- Animation (no timers, no visual state)
- Analytics (no telemetry, no tracking)
- Safety (no clinical rules, no escalation)

### Layering

Mirrors the proven pattern from `@core/runtime`:

```
src/core/execution-session/
├── index.ts                       — public barrel
├── domain/                        — pure types
├── application/                   — Aggregate Root + plumbing
└── util/                          — pure projections
```

### Invariants (Aggregate Root guarantees)

1. Identity never changes after construction.
2. Plan reference never changes.
3. Event log is append-only; past events are frozen.
4. State transitions follow the `legalTransitions` table.
5. Snapshot version monotonically increases with state changes.

### Compatibility with Runtime

The Session does NOT consume Runtime events directly. It's driven by
its own API (`start`, `pause`, `recordPhaseChange`, ...). A future
**Session Engine** (Sprint 6+) will translate Runtime events into
Session API calls. This keeps the Session testable in isolation
without depending on Runtime.

---

## Alternatives Considered

### Alternative A — Make the Runtime itself the Session

**Rejected.** The Runtime is engine-level (10 states, owns 3 engines).
Adding `idle`, `preparing`, `interrupted` to it would conflate two
audiences (engine integrators vs. UI/Session consumers) and break
the clean FSM contract.

### Alternative B — Compute Session state from Runtime events at the UI layer

**Rejected.** Duplicates the projection logic across every consumer
(UI, Audio Engine, Analytics). The brief explicitly requires a single
source of truth.

### Alternative C — Make Session a plain data interface, not an Aggregate

**Rejected.** A plain interface can't enforce invariants. The brief
lists "Aggregate Root" and "imutabilidade" as hard requirements.
Behavior + invariants belong together.

---

## Consequences

### Positive

- **One canonical model.** Every consumer reads from the same
  `ExecutionSession`. No more divergent projections.
- **DDD-aligned.** Identity, invariants, and event sourcing match the
  Aggregate Root pattern, making the code reviewable against industry
  vocabulary.
- **Testable in isolation.** No engine, no network, no clock — only a
  controllable `now` function. Tests run fast and deterministic.
- **Runtime-agnostic.** Session does not depend on `@core/runtime`,
  making it usable in tests and tools that don't need the full engine
  stack.
- **Event sourcing** enables future replay-based debugging, time
  travel, and analytics without code changes.

### Negative

- **Dual state machines.** Runtime has 10 states, Session has 8. Two
  sources of truth require a Session Engine to bridge them. The brief
  defers the bridge to a later sprint.
- **More boilerplate.** 13 source files for what is conceptually a
  single concept. Mitigated by the clear layering and barrel exports.
- **No clock injection by default.** Default clock is `Date.now()`.
  Tests must inject a fake clock to drive deterministic time. This is
  documented and tested.

### Compliance

- ✅ `@araflow/32_FINAL_PRODUCT_DECISIONS.md` — pure domain, no UI,
  no persistence.
- ✅ `@araflow/33_ENGINEERING_BLUEPRINT.md` — layered architecture
  (domain / application / util), barrel exports, Result-based API,
  ≥95% coverage.
- ✅ Sprint 5 brief — DDD Aggregate Root, immutable snapshots,
  event sourcing, timeline, metrics, invariants, tests, documentation.
- ✅ Frozen engines — Session depends only on `@araflow/shared-contracts`
  and `@core/protocol-compiler` (for the plan type, which is frozen at
  v1.0.0).

---

## Implementation notes

- All mutable state lives on the Aggregate Root. Util functions are
  pure (input → output, no side effects).
- `Object.freeze` is applied to all returned objects (snapshots,
  metrics, events, timeline).
- The `SessionEventLog` produces a new frozen array on each append;
  old arrays remain accessible (snapshot semantics).
- Branded types (`SessionId`, `ProtocolId`, `ExecutionPlanId`) come
  from `@araflow/shared-contracts` where available; `ExecutionPlanId`
  is defined in-domain for clarity.
- 96 unit tests covering all transitions, snapshots, timeline,
  metrics, event log, invariants, errors, concurrency, and dispose.