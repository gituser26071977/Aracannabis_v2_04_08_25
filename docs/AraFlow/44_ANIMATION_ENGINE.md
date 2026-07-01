# AraFlow — Animation Engine

| Field      | Value                            |
| ---------- | -------------------------------- |
| Module     | `@core/animation-engine`         |
| Version    | 1.0.0                            |
| Date       | 2026-07-01                       |
| Status     | ✅ Completed — Sprint 8          |
| Parent     | Sprint 7 (Session Persistence)   |
| Next       | Sprint 9 (First Visual Experience) |

---

## Mission

Convert events emitted by **Runtime**, **Breath**, **Timer**, and
**Session** into a deterministic, drift-free stream of immutable
`AnimationFrame`s. The Engine is the single, presentation-agnostic
source of truth for "what should be on screen right now".

It contains **no UI, no React, no React Native, no Skia, no SVG, no
Lottie, no Canvas**. Sprint 9 will plug those backends onto this
Engine; the Engine itself never imports a rendering library.

---

## Architecture

```
                  +--------------------+
   Runtime ──►    |                    |
   Breath ──►     |  AnimationEngine   | ──► AnimationFrame stream
   Timer ──►      |  (4-state FSM)     |     (frozen, tagged-union
   Session ──►    |                    |      events)
                  +────────┬───────────┘
                           │
                  +────────▼───────────+
                  |  AnimationFrame   |  ← immutable, frozen
                  |  ─ timestamp      |
                  |  ─ phase          |
                  |  ─ progress       |
                  |  ─ radius         |
                  |  ─ opacity        |
                  |  ─ scale          |
                  |  ─ easingCurve    |
                  |  ─ breathingDepth |
                  |  ─ label          |
                  |  ─ remainingTime  |
                  +────────────────────+
```

The Engine reads from upstream engines **only** through their public
event APIs (`subscribe`). It never pokes at internal state. It writes
to its own private FSM and emits downstream frames through its own
event stream.

---

## Why a dedicated Engine

The Core produces dozens of events per second (timer ticks, breath
phase changes, runtime lifecycle, session transitions). Mapping these
to visual state — *is the user inhaling? how full should the circle
be? which easing should I apply?* — is non-trivial:

1. The mapping must be **deterministic** — same events at same times
   produce the same frames.
2. The mapping must be **drift-free** — no clock skew between the
   source of truth (Timer) and what the renderer sees.
3. The mapping must be **allocation-light** — React renderers may
   subscribe at 60 Hz; we don't want GC pauses.
4. The mapping must be **isolated** from rendering — different
   backends (Skia/SVG/Lottie/Canvas) need the same input.

A pure projection layer (no `useEffect`, no DOM, no Skia, no React)
satisfies all four. This Engine is that layer.

---

## Module structure

```
mobile/src/core/animation-engine/
├── index.ts                                  — public barrel + version
├── domain/
│   ├── AnimationPhase.ts                     — 6 phases + labels
│   ├── AnimationFrame.ts                     — immutable frame shape + isFrame
│   ├── AnimationConfig.ts                    — visual knobs + defaults
│   ├── AnimationEngineState.ts               — 4-state FSM
│   ├── AnimationEvent.ts                     — tagged-union events
│   └── AnimationMetrics.ts                   — framesEmitted, phaseChanges, etc.
├── application/
│   ├── AnimationEngine.ts                    — main Facade (12 methods)
│   ├── AnimationEngineDeps.ts                — constructor options
│   └── AnimationEventStream.ts               — tagged-union dispatcher
└── util/
    ├── frame-computation.ts                  — pure projection
    └── phase-mapping.ts                      — Breath/Session/Runtime → Animation
```

---

## Public API (12 methods + factory)

```ts
// Construction
const engine = createAnimation({ runtime, breath?, timer?, session?, config?, now?, onListenerError? });

// Lifecycle
engine.start(): void;
engine.pause(): void;
engine.resume(): void;
engine.dispose(): void;

// Observation
engine.subscribe(listener): () => void;
engine.state(): AnimationEngineState;
engine.phase(): AnimationPhase;
engine.easingCurve(): CurveName;
engine.currentFrame(): AnimationFrame;
engine.metrics(): AnimationMetrics;
engine.id(): string;
engine.update(nowMs?: number): AnimationFrame;
```

`update()` is the RAF tick: pass `nowMs` from your rAF callback or
let the Engine read its injected clock. Either way, the next frame is
recomputed and emitted.

---

## Frame shape

Every `AnimationFrame` is deeply frozen and contains:

| Field               | Type                | Range      | Meaning                                          |
| ------------------- | ------------------- | ---------- | REDACTED |
| `timestamp`         | `number` (ms)       | monotonic  | Capture time                                     |
| `phase`             | `AnimationPhase`    | enum       | Current visible phase                            |
| `normalizedProgress`| `number`            | [0, 1]     | Linear progress within the current phase         |
| `radius`            | `number`            | [0, 1]     | Visual radius of the breath circle               |
| `opacity`           | `number`            | [0, 1]     | Visual opacity                                   |
| `scale`             | `number`            | [0, 1]     | Visual scale multiplier                          |
| `easingCurve`       | `CurveName`         | enum       | Easing curve applied to this frame's progress    |
| `breathingDepth`    | `number`            | [0, 1]     | Amplitude (0 = trough, 1 = peak)                 |
| `label`             | `string`            | —          | Human-readable phase label                       |
| `remainingTime`     | `number` (ms)       | ≥ 0        | Time remaining in the current phase              |

`radius`/`opacity`/`scale` are pre-computed for the active phase so
renderers don't need their own easing/lerp logic — they just consume
the numbers.

---

## Phase mapping

The Engine bridges three upstream phase vocabularies to one
presentation vocabulary:

```
Animation    Source A           Source B            Source C
─────────    ────────           ────────            ────────
inhale    ←  inhaling         —                    —
hold      ←  holdAfterInhale  —                    —
              holdAfterExhale —                    —
exhale    ←  exhaling         —                    —
preparing ←  —                 starting             preparing
completed ←  —                 completed            completed
idle      ←  —                 uninitialized,       idle
                              errored, stopped     cancelled, failed
```

Three pure functions do the translation:

- `mapBreathPhase(phase): { animation, hold }` — maps a Breath phase
  to an Animation phase + a `HoldPosition` (`peak`/`trough`/`none`).
- `mapSessionState(state): AnimationPhase` — coarse session-state
  mapper.
- `mapRuntimeState(state): AnimationPhase` — coarse runtime-state
  mapper.

`hold` carries the peak/trough distinction lost by collapsing
`holdAfterInhale` and `holdAfterExhale` into the single `hold`
Animation phase. The frame's `breathingDepth` reflects this so
renderers don't need to track it.

---

## Curve reuse

The Engine consumes **`resolveCurve`** from `@core/breath-engine` —
the same easing curves used for breath mechanics. A change to a
curve's shape ripples through to the animation automatically. No
duplication, no drift.

Supported curves: `linear`, `easeIn`, `easeOut`, `easeInOut`, `sine`,
`cosine`, `bezier`.

---

## FSM (4 states)

```
                ┌──────────────────┐
                │  idle            │  ── start() ──► running
                │  (constructed)   │  ── dispose() ► disposed
                └──────────────────┘
                          ▲       │
                          │       ▼
              ┌───────────┴──────────────────────┐
              │  running  ── pause() ──► paused  │
              │     ▲                       │    │
              │     └───── resume() ────────┘    │
              │                                  │
              │  ── dispose() ──► disposed       │
              └──────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  disposed (terminal)│
              └─────────────────────┘
```

`disposed` is terminal: subsequent `start()`/`pause()`/`resume()` are
no-ops.

---

## Lifecycle ownership

The Engine owns no upstream engine — it **subscribes** to them and
forwards their events into its own FSM. On `dispose()` it unsubscribes
and clears its listener set, so renderers (and the Event Stream)
release cleanly.

The Engine also exposes `sessionSnapshot()` for debugging — it
returns whatever the injected `ExecutionSession` exposes (or `null`
when no session was injected).

---

## Drift-free updates

There are three update paths:

1. **Event-driven.** A Runtime/Breath/Session event arrives → Engine
   re-derives the current phase, computes a fresh frame, emits it.
2. **Tick-driven.** A `TimerEngine` tick arrives → Engine re-runs
   `update(now)` and emits a fresh frame. This is what keeps the
   animation in lock-step with the master clock without depending on
   `requestAnimationFrame`.
3. **Manual.** A consumer calls `engine.update(nowMs)` directly
   (e.g. inside an rAF callback).

All three converge on the same pure projection: `computeAnimationFrame`
takes (phase, progress, hold, config, timestamp, remainingTime) and
returns a frozen frame. Side-effect-free. Deterministic.

---

## Event stream

The Engine emits a tagged-union event stream:

```ts
type AnimationEvent =
  | { type: 'animation-frame';          monotonicMs: number; frame: AnimationFrame }
  | { type: 'animation-engine-started'; monotonicMs: number }
  | { type: 'animation-engine-paused';  monotonicMs: number; frozenFrame: AnimationFrame }
  | { type: 'animation-engine-resumed'; monotonicMs: number }
  | { type: 'animation-engine-disposed';monotonicMs: number };
```

A re-entrant `subscribe()` during emit does **not** receive the
current event (snapshot pattern). A throwing listener is routed to
`onListenerError` and does not break emission to other listeners.

---

## Metrics

The Engine tracks four counters:

- `framesEmitted` — total frames emitted.
- `updates` — total `update()` calls.
- `phaseChanges` — total phase transitions.
- `lastFrameTimestamp` — last emitted frame's monotonic timestamp.
- `attachedSince` — timestamp of the most recent `start()`.

Useful for renderers that need to detect "stuck" frames or surface
frame rate to the UI.

---

## Compliance

- ✅ NO UI / React / React Native / Skia / SVG / Lottie / Canvas.
- ✅ Pure projection: same inputs → same outputs.
- ✅ Deterministic: curves + phase mapping are pure.
- ✅ Drift-free: Timer ticks re-trigger `update()`.
- ✅ Listener isolation: throwing listener → `onListenerError`.
- ✅ Re-entrant safe: late subscribers do not see the current event.
- ✅ Frozen engines: Runtime / Breath / Timer / Session are not
  modified.

---

## What's next (Sprint 9)

The brief explicitly defers:

- React Native Skia renderer
- SVG fallback
- Lottie alternative
- Canvas (web)
- Frame interpolation between RAF ticks
- Audio sync (next sprint after visualization)
- Touch / gesture handlers
- Themed colors / dark mode

Sprint 9 plugs a Skia-based renderer onto this Engine and produces
the first AraFlow visual. The Engine's contract is the seam.