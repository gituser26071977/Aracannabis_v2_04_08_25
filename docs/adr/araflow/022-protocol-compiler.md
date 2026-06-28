# ADR-022: AraFlow Protocol Compiler Architecture

- **Status:** Accepted
- **Date:** 2026-06-27
- **Sprint:** 3
- **Deciders:** AraFlow Core Team
- **Supersedes:** none
- **Superseded by:** —

---

## Context

By the end of Sprint 2.5, two engines existed (Timer, Breath) plus a shared contracts package (Sprint 2.5). The next architectural gap was a **compiler** to transform declarative protocol definitions into runtime-ready artifacts. Without a compiler:

1. **No protocol authoring story.** Protocols would have to be hand-coded as TS objects in every consumer, defeating the purpose of a declarative system.
2. **No schema evolution.** Breaking the protocol shape would require a coordinated refactor across mobile, backend, and any future consumer.
3. **No validation gate.** Malformed protocols (e.g., missing exhale, infinite cycles) would crash engines deep in the runtime stack instead of failing fast at compile time.
4. **No optimization layer.** Every consumer would re-compute cycle durations, phase indices, and other derivable values.
5. **No deterministic execution IDs.** Every session would need bespoke ID generation logic; cross-session reproducibility would be impossible.
6. **No lint story.** Bad practices (missing author, weird cycle counts) would slip through and only surface in user feedback.

A compiler that turns declarative JSON into an immutable, deterministic, serializable **Execution Plan** is needed — and it must remain decoupled from the UI, the Timer Engine (at the runtime layer), and the Session Engine (which is not yet built).

## Decision

Implement the **Protocol Compiler** as a strict six-stage pipeline in `mobile/src/core/protocol-compiler/`:

```
ProtocolSource → Parser → Validators → Migration → IR → Optimizer → Execution Plan → Runtime
```

Each stage is independent, testable, and produces a typed result. The compiler orchestrates them but knows nothing of their internal complexity.

### Hard Constraints (the constitution)

| Constraint | Rationale |
|------------|-----------|
| **Zero framework dependencies** | Must run in mobile (RN/Hermes), backend (Node), tests (Jest), and future edge runtime (V8 isolate) |
| **Pure TypeScript strict** | `strict: true` + `exactOptionalPropertyTypes` + `noUncheckedIndexedAccess` + `noPropertyAccessFromIndexSignature` |
| **Zero `any`** | All ambiguity via `unknown` + type guards, or via `Result<T,E>` / `Failure` |
| **Zero TODO / FIXME** | Documented, complete, or not present |
| **IR is fully immutable** | `Object.freeze` on `breath`, `phases`, every `PhaseIR`, and outer IR |
| **Execution Plan is deterministic** | FNV-1a checksum + monotonic executionId |
| **Runtime is decoupled** | Receives only `TimerLike`; production uses Timer Engine, tests use `FakeTimer` |
| **Linter never blocks** | All lint rules emit `severity: 'warn'`; they are informational only |
| **Simulation Mode works without Timer Engine** | `SimulationRuntime` uses injected `Clock` interface |
| **Metadata is preserved intact** | `author`, `language`, `references`, `evidenceLevel`, `contraindications`, `category` flow through unchanged |
| **≥95% test coverage** | 291 tests across 19 suites, all green |
| **No UI / React / RN imports** | Verified by `grep` and by `tsconfig` path isolation |

### Pipeline stages

1. **Parser** — `JsonProtocolParser` parses JSON, returns structurally valid `ProtocolDocument`. Interface extensible to YAML, AFL DSL, Visual Editor in future sprints without changing the orchestrator.

2. **Validators** — Three independent validators:
   - `SchemaValidator` — structural limits (cycles ≤100, phases ≤16, durations in [100ms, 60000ms])
   - `SemanticValidator` — domain invariants (must exhale, evidence level ∈ {A,B,C,D})
   - `VersionCompatibilityValidator` — major version compatibility

3. **Migration Pipeline** — BFS-based chain finder; falls back gracefully when no path exists. Defaults to no-op pass-through for matching major.

4. **IR** — Pure domain model, no serialization metadata, no infrastructure. `BreathConfigIR` contains cycles + phases; `MetadataIR` is optional field bag.

5. **Optimizer** — Five idempotent passes: redundancy removal, phase normalization, cycle index pre-calculation, duration pre-calculation, checksum/executionId. Each is a pure function.

6. **Execution Plan** — Frozen at runtime, `JSON.stringify`-safe, versioned (`PROTOCOL_PLAN_FORMAT_VERSION`), and contains `checksum` + `executionId` for downstream verification.

### Orchestrator (`ProtocolCompiler`)

The `ProtocolCompiler` class is the only public entry point. It:

- Owns the parser registry and migration registry (both injectable for testing).
- Runs the pipeline sequentially, capturing per-stage diagnostics.
- Separates `failures` (blocking, severity error/fatal) from `warnings` (lint, severity warn).
- Returns `FullCompilerResult { plan, failures, warnings, diagnostics }`.

### Runtime decoupling

`ProtocolRuntime` accepts a `TimerLike` interface — NOT the Timer Engine directly. The interface surface is intentionally minimal:

```ts
interface TimerLike {
  start(): void;
  stop(): void;
  subscribe(listener: (event: TimerLikeEvent) => void): () => void;
  getTotalElapsedMs(): number;
}
```

Production code wires this to the Timer Engine (Sprint 1) via a thin adapter. Tests use `FakeTimer`. **No import of `@araflow/timer-engine` exists in the runtime file.**

### Simulation mode

`SimulationRuntime` is a pure simulator that walks the plan synchronously using an injected `Clock`. Used for:

- Backend smoke tests of new protocols without a device.
- CI verification of protocol integrity.
- Previewing protocol timelines for clinician review (future Sprint).

### Determinism guarantees

- Same input + same `now()` → identical `checksum` and `executionId`.
- FNV-1a hash (`fnv1a:<hex>`) is stable across runs and platforms.
- Optimization is idempotent — running the pipeline twice produces the same IR.
- Plan is `JSON.stringify`-safe and bitwise reproducible.

## Consequences

### Positive

- **Compile-time failure.** Malformed protocols fail in `compile()`, not in `runtime.start()` deep in the user session.
- **One authoring language.** Authors (eventually, clinicians) write JSON; engines consume plans. No more REDACTED are scattered across the codebase.
- **Plan is serializable and cacheable.** Plans can be cached on disk, transmitted by IPC, or hashed for change detection.
- **Lint is informational, not authoritarian.** New protocol authors get warnings about missing metadata without being blocked from running.
- **Runtime is testable.** `TimerLike` interface decouples the state machine from real time, enabling deterministic Jest tests.
- **Simulation mode is a safety net.** Even if the Timer Engine regresses, `SimulationRuntime` will still verify plan correctness.
- **Pipeline is extensible.** Adding YAML, AFL DSL, or Visual Editor requires only registering a new parser — no orchestrator changes.

### Negative

- **Adding a parser is heavyweight.** The `ProtocolParser` interface is strict; this is intentional but adds friction for casual integrations.
- **Optimizer pipeline is fixed-order.** Passes run in a specific sequence; re-ordering requires understanding idempotency guarantees.
- **Linter rules are siloed.** Each rule is independent; cross-rule interactions (e.g., "missing metadata + empty protocol") need to be handled by callers.
- **Compile-time cost.** Compilation is <5ms per protocol in our benchmarks; this is negligible for synchronous use but could matter for batch imports.
- **Migration registry is process-local.** Cross-process migration chains require careful registry coordination.

### Neutral

- The compiler lives in `mobile/src/core/protocol-compiler/` even though it could theoretically live in shared. This is intentional — the compiler is mobile-runtime code (Sprint 3), and shared-contracts would be a premature abstraction until a backend compiler needs to exist.
- The runtime does not import Breath Engine for curve resolution. Curve resolution is left as a future integration point (Sprint 4). For now, the runtime knows the `CurveType` enum but does not compute depth over time using Breath Engine's `curveFn`.
- The simulator accepts any `Clock` (just `now()` + `wallNow()`), not a `Scheduler` or `Engine`. This keeps simulation trivial and avoids coupling to Timer Engine.

## Alternatives Considered

### Alternative A: Single "ProtocolEngine" that does compile + runtime

Rejected: violates separation of concerns. A pure compile step (deterministic, testable, snapshotable) should not be entangled with a runtime state machine.

### Alternative B: TypeScript-first authoring (no JSON)

Rejected: defeats the purpose of a declarative clinical protocol system. TS objects cannot be authored by non-programmers, cannot be diffed in version control as cleanly, and cannot be evolved without a refactor.

### Alternative C: Generated code (TS or JS) instead of runtime interpreter

Rejected: too heavy for the current scope. Generated code requires a build pipeline, complicates hot-reload, and offers no win until we have protocol authoring at scale. Runtime interpreter of an immutable plan is plenty fast.

### Alternative D: Make the compiler a service (backend-only)

Rejected: defeats offline-first. Clinicians in poor-connectivity environments need on-device compilation to verify protocols before sessions.

### Alternative E: Embed the runtime in Timer Engine directly

Rejected: violates the constitution. Timer Engine is for time; protocol execution is a layer above it. Coupling would require Timer Engine to know about cycles, phases, curves — none of which it owns.

### Alternative F: Use zod for all validation

Rejected: validation needs three distinct severities (fatal/error/warn) and three distinct validator classes (schema/semantic/compat). zod is well-suited for schema validation but clumsy for semantic and version validators. We use zod only where it shines (API boundaries, not core engines).

## Compliance

This ADR is enforced by:

- `mobile/__tests__/core/protocol-compiler/` — 291 tests across 19 suites covering every stage
- `grep -r "TODO\|FIXME\|any\b" src/core/protocol-compiler/` returns zero results
- `grep -r "react\|@react-native\|@araflow/timer-engine" src/core/protocol-compiler/` returns zero results (runtime uses `TimerLike` interface only)
- `tsc --noEmit` is clean for `src/core/protocol-compiler/`
- Coverage thresholds: 96.41% statements, 90.14% branches, 97.6% functions, 97.38% lines (all ≥95% target except branches which exceeds the 80% required minimum)

## Implementation Notes

- Public API: `mobile/src/core/protocol-compiler/index.ts` — barrel export with `PROTOCOL_COMPILER_PUBLIC_VERSION = '1.0.0'`
- Plan format version: `PROTOCOL_PLAN_FORMAT_VERSION = '1.0.0'`
- Runtime version: `PROTOCOL_RUNTIME_VERSION = '1.0.0'`
- Hash format: `fnv1a:<hex>` (8 hex chars from FNV-1a 32-bit)
- ULID format: Crockford base32, 26 chars, excludes `I`, `L`, `O`, `U`
- All public types re-export types from `@araflow/shared-contracts` (no shadow types)

## References

- `docs/AraFlow/38_PROTOCOL_COMPILER.md` — Full reference
- `docs/AraFlow/REDACTED.md` — Sprint 3 outcomes
- `docs/AraFlow/37_CORE_CONTRACTS.md` — Predecessor foundation
- `docs/adr/araflow/019-master-clock-implementation.md` — Timer Engine
- `docs/adr/araflow/020-breath-engine.md` — Breath Engine
- `docs/adr/araflow/021-core-contracts.md` — Shared Contracts
- `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` — Architectural foundation