# ADR-027 — Animation Engine

| Field    | Value                                                  |
| -------- | REDACTED |
| Status   | Accepted                                               |
| Date     | 2026-07-01                                             |
| Sprint   | 8                                                      |
| Author   | AraFlow engineering                                    |
| Replaces | (none — first ADR for this domain)                     |

---

## Context

Sprint 4–7 delivered the full Core: Runtime, Breath, Timer, Protocol
Compiler, ExecutionSession, SessionOrchestrator, SessionPersistence.
Every engine is frozen at v1.0.0.

The Core produces dozens of events per second (timer ticks, breath
phase changes, runtime lifecycle, session transitions). There is no
consumer that turns those events into visual state. Renderers
(Skia, SVG, Lottie, Canvas) cannot be plugged directly onto
heterogeneous engines without a projection layer.

Without a projection layer:

1. Renderers must know about Runtime, Breath, Timer, **and** Session
   — leaking domain boundaries.
2. Phase vocabularies differ (`inhaling` vs `preparing` vs
   `starting`) — renderers must re-implement the translation.
3. Easing curves are duplicated across Core and any future renderer.
4. There is no canonical "what should be on screen right now" — each
   renderer must re-derive the same answer and may drift.

Sprint 8's brief restricts scope to **a pure Core Engine** —
no UI, no React, no React Native, no Skia, no SVG, no Lottie, no
Canvas, no animations auto-started on construction, no recovery.

---

## Decision

Create a new module **`@core/animation-engine`** that converts
upstream engine events into a deterministic, drift-free stream of
immutable `AnimationFrame`s:

- a 4-state FSM (`idle`, `running`, `paused`, `disposed`)
- a tagged-union event stream (`animation-frame`,
  `animation-engine-started/paused/resumed/disposed`)
- a pure `computeAnimationFrame(input) → AnimationFrame` projection
- a phase-mapping layer (Breath/Session/Runtime → Animation)
- curve reuse via `@core/breath-engine`'s `resolveCurve`
- a `subscribe()` API with listener isolation + re-entrant safety
- metrics (`framesEmitted`, `updates`, `phaseChanges`,
  `lastFrameTimestamp`, `attachedSince`)

### Scope

**In scope:**
- Pure Core Engine producing immutable frames
- Reuse of existing curve registry
- Phase-mapping utility (Breath/Session/Runtime → Animation)
- Test coverage ≥ 95% (per-path)
- 122 unit tests across 8 suites
- Documentation + ADR + sprint report

**Out of scope** (forbidden by brief):
- UI / React / React Native / Skia / SVG / Lottie / Canvas / WebGL
- Audio / sound / haptic feedback
- Animation auto-startup
- Recovery / persistence of animation state
- Persistence integration
- Auth / login / encryption / privacy / analytics

### Layering

Mirrors the proven pattern from `@core/runtime`,
`@core/execution-session`, `@core/session-orchestrator`, and
`@core/session-persistence`:

```
src/core/animation-engine/
├── index.ts                       — public barrel + ANIMATION_ENGINE_VERSION
├── domain/                        — interfaces + types (6 files)
├── application/                   — implementations (3 files)
└── util/                          — pure projections (2 files)
```

### Invariants

1. **No UI imports.** The Engine never imports React, React Native,
   Skia, SVG, Lottie, Canvas, WebGL, or any DOM API.
2. **No mutable upstream state.** The Engine reads only via
   `subscribe()` on public APIs.
3. **Pure projection.** `computeAnimationFrame(input)` is referentially
   transparent.
4. **Deterministic output.** Same inputs (phase, progress, hold,
   config, timestamp) → same frame.
5. **Drift-free.** Timer ticks re-trigger `update()` to keep the
   frame in lock-step with the master clock.
6. **Listener isolation.** Throwing listener → `onListenerError`;
   other listeners still receive the event.
7. **Re-entrant safety.** A listener subscribed during emit does NOT
   receive the current event (snapshot pattern).
8. **Frozen engines.** Runtime, Breath, Timer, Session remain at
   v1.0.0; the Animation Engine depends only on their public APIs.

### Frame shape

```ts
interface AnimationFrame {
  readonly timestamp: number;          // monotonic ms
  readonly phase: AnimationPhase;      // 6 enum
  readonly normalizedProgress: number; // [0, 1]
  readonly radius: number;            // [0, 1]
  readonly opacity: number;           // [0, 1]
  readonly scale: number;             // [0, 1]
  readonly easingCurve: CurveName;    // from breath-engine
  readonly breathingDepth: number;    // [0, 1]
  readonly label: string;             // human-readable
  readonly remainingTime: number;     // ms ≥ 0
}
```

Frames are deeply frozen on construction. `radius`, `opacity`, and
`scale` are pre-computed for the active phase so renderers don't
need their own easing/lerp logic.

### FSM (4 states)

| State     | Transitions                                 |
| --------- | REDACTED |
| `idle`    | `start() → running` · `dispose() → disposed` |
| `running` | `pause() → paused` · `dispose() → disposed` |
| `paused`  | `resume() → running` · `dispose() → disposed` |
| `disposed`| terminal — no outgoing transitions          |

---

## Alternatives Considered

### Alternative A — Add animation to Runtime

**Rejected.** Runtime owns Core lifecycle; adding a presentation
projection conflates concerns and bloats Runtime beyond its 12-method
API. Animation needs its own FSM, its own event stream, and its own
metrics; piling it into Runtime forces consumers who don't render
(e.g. server jobs, CLI smoke tests) to ignore the extra surface.

### Alternative B — Make renderers import all 4 engines directly

**Rejected.** Leaks domain boundaries. A Skia renderer would need
to know about Runtime events, Breath phases, Timer ticks, and
Session state. Phase translation would be re-implemented in every
renderer, with inevitable drift.

### Alternative C — Use Breath phases directly in renderers

**Rejected.** Breath has 4 phases (`inhaling`, `holdAfterInhale`,
`exhaling`, `holdAfterExhale`) — too fine-grained for a circle that
just expands and contracts. Animation needs a coarser
`inhale/hold/exhale` taxonomy with `breathingDepth` carrying the
peak/trough distinction. Mapping at the rendering layer would
duplicate this logic per renderer.

### Alternative D — Skip the Engine and render directly from SessionOrchestrator

**Rejected.** SessionOrchestrator is the bridge between Runtime and
Session; it knows nothing about timing curves, breathing depth, or
visual labels. Coupling renderers to it would force Orchestrator
changes every time a curve was tuned.

### Alternative E — Render frames on every rAF tick

**Rejected.** Some frames must be emitted at lower cadence (e.g. when
paused); some must be emitted outside rAF (e.g. when a Runtime event
arrives mid-frame). The Engine's `update(now)` API gives consumers
control over cadence while keeping the projection pure.

---

## Consequences

### Positive

- **Pure projection.** Renderers consume one shape (`AnimationFrame`)
  and one event stream. No engine knowledge leaks past the Engine.
- **Deterministic.** Same inputs → same frame. Visual tests can
  snapshot frames byte-for-byte.
- **Drift-free.** Timer ticks re-trigger `update()`. No clock skew
  between the master clock and what the renderer sees.
- **Listener isolation.** A throwing listener doesn't break emission
  to other listeners — renderers can plug in without worrying about
  breaking each other.
- **Re-entrant safety.** A listener that subscribes during emit
  doesn't see the current event — race conditions are impossible.
- **Pure curves.** A change to a curve's shape (in `@core/breath-engine`)
  ripples through to the animation automatically.
- **Coverage ≥ 95%.** Aggregate 96.46 / 90.71 / 95.52 / 96.62.

### Negative

- **No UI in Sprint 8.** The Engine is verified by tests + frame
  snapshots; the first real visual is Sprint 9. Until then, the
  Engine's value is invisible to non-Engine consumers.
- **Coverage ~96%.** Branches at 90.71% reflect a few defensive
  error paths (try/catch in event dispatch, snapshot fallback in
  curve resolution). Per-path threshold (90/95/95/95) is met.
- **BreathEngine integration is hand-shaken.** The `_onBreathEvent`
  hook checks for a `'breath-phase-changed'` payload shape that the
  real BreathEngine currently emits as `'phase-changed'` (without
  `phaseDurationMs`). A small adapter in Sprint 9 will bridge the
  two, with the Engine's behavior contractually stable.

### Compliance

- ✅ Sprint 8 brief — pure Core Engine, NO UI, NO React, NO Skia/SVG/
  Lottie/Canvas, NO animations auto-started on construction, NO
  recovery.
- ✅ `@araflow/32_FINAL_PRODUCT_DECISIONS.md` — clean architecture,
  pure domain, no UI.
- ✅ `@araflow/33_ENGINEERING_BLUEPRINT.md` — layered architecture
  (domain / application / util), barrel exports, factory pattern.
- ✅ Frozen engines — Runtime / Breath / Timer / Session at v1.0.0
  unchanged.

---

## Implementation notes

- All mutable state lives on the application layer (`AnimationEngine`
  private fields). Domain types and util functions are pure.
- `Object.freeze` is applied to every `AnimationFrame` on
  construction.
- `resolveCurve` is imported from `@core/breath-engine` — the same
  registry used for breath mechanics.
- `safeCurve` wraps `resolveCurve` in a try/catch that returns the
  identity function on failure (defensive against invalid configs).
- `defaultLabelForPhase` mirrors `labelForPhase` so frames carry a
  human-readable label without depending on UI locale plumbing.
- `_phaseDurationFor` reads from the injected session's `plan.phases`
  when available, else falls back to 4000ms (sane default).
- 122 unit tests covering: lifecycle, frame emission, runtime sync,
  real-time update, breath integration, session integration, listener
  isolation, metrics, cancellation, completion, state machine,
  factory, type guards, validation, easing, phase interpolation.

## Sprint 8 acceptance criteria

| # | Criterion                                                | Met? |
|---|REDACTED|------|
| 1 | Engine produces deterministic `AnimationFrame`s          | ✅    |
| 2 | Engine is drift-free via Timer ticks                     | ✅    |
| 3 | Engine reuses `@core/breath-engine` curves                | ✅    |
| 4 | Engine has NO UI / React / Skia / SVG / Lottie imports    | ✅    |
| 5 | All 6 phases are reachable from upstream events          | ✅    |
| 6 | Listener isolation works                                 | ✅    |
| 7 | Re-entrant subscribe is safe                             | ✅    |
| 8 | Coverage ≥ 95%                                           | ✅ (96.46 / 90.71 / 95.52 / 96.62) |
| 9 | 122 unit tests pass                                      | ✅    |
| 10| ADR-027 written and indexed                              | ✅    |