# ADR-021: AraFlow Shared Contracts as Technical Constitution

- **Status:** Accepted
- **Date:** 2026-06-25
- **Sprint:** 2.5
- **Deciders:** AraFlow Core Team
- **Supersedes:** partial — `016-npm-workspaces`, `017-typescript-strict-branded`

---

## Context

By the end of Sprint 2, two engines existed (Timer, Breath) across two runtime targets (mobile RN, backend Node). Both engines independently defined:

- Branded `ProtocolId` (ULID validation duplicated)
- Branded `Duration` (range checks duplicated)
- `BreathPhase` enum (two slightly-different naming conventions)
- `Result<T,E>`-like helpers (different shapes per file)
- Error types (different `code`/`severity` semantics)

Symptoms:

1. **Type identity issues** — `BreathPhase` in mobile didn't structurally match `BreathPhase` in backend, even though the values were identical.
2. **Inconsistent validation** — `Duration` rejected negative integers in mobile but accepted them in backend.
3. **Repeated code** — 6 different `isNonEmptyString` implementations across the codebase.
4. **No shared documentation** — new engines couldn't know which types to use.

A single source of truth was needed.

## Decision

Establish `@araflow/shared-contracts` as the **Technical Constitution of AraFlow**. Every type, enum, pattern, error, interface, and event is defined exactly once, in this package, and imported everywhere else.

### Hard Constraints (the constitution)

| Constraint | Rationale |
|------------|-----------|
| **Zero framework dependencies** | Must run in mobile (RN/Hermes), backend (Node 20), and edge (V8 isolate) without polyfills |
| **Pure TypeScript strict** | `strict: true` + `exactOptionalPropertyTypes` + `noUncheckedIndexedAccess` |
| **Zero `any`** | All ambiguity via `unknown` + type guards, or via `Result<T,E>` |
| **Branded primitives** | `Duration` ≠ `Timestamp` ≠ `number` at the type level |
| **Frozen at runtime** | `Result`, `Option`, `Either`, `Failure` use `Object.freeze` |
| **Errors carry code + severity + context** | Consistent logging and IPC across boundaries |
| **100% test coverage** | Constitution is law; unverified clauses are not in force |
| **Exhaustive enums** | Each enum ships with type, tuple, predicate, and rank (where applicable) |

### What goes in shared-contracts

- **Value Objects** — Branded primitives with validation: `Duration`, `Timestamp`, `ProtocolId`, `EngineId`, `SemanticVersion`, etc.
- **Enums** — Canonical state values: `EngineState`, `BreathPhase`, `Priority`, `Severity`.
- **Patterns** — `Result<T,E>`, `Option<T>`, `Either<L,R>`, `Failure`.
- **Utilities** — `generateUuidV4`, `TIME_UNITS`, `DeepReadonly<T>`.
- **Interfaces** — `Engine`, `Disposable`, `Subscription`, `Clock`, `Scheduler`, `Logger`, `MetricsCollector`, `EventBus`, `Compiler`, `ProtocolSourceLoader`.
- **Events** — Canonical event types: `EngineStartedEvent`, `TickEvent`, `PhaseChangedEvent`, etc.
- **Errors** — `AppError` + typed subclasses: `ValidationError`, `CompilationError`, `EngineError`, `ProtocolError`, `TimerError`, `BreathError`.

### What does NOT go in shared-contracts

- Engine implementations (live in `mobile/src/core/<engine>/`)
- React / RN components (live in `mobile/src/features/`)
- Database schemas (live in `backend/src/`)
- Business logic (lives where used)
- Anything with platform-specific imports

### Migration rule

When a new concept appears that two places will share:
1. Add it to `shared-contracts` FIRST (with tests).
2. Bump `SHARED_CONTRACTS_VERSION` (currently `2.5.0`).
3. Migrate consumers in a single commit.

If only one place needs it, leave it local.

## Consequences

### Positive

- **One identity per concept.** `Duration` is `Duration` everywhere; renaming it is a single edit.
- **Type narrowing works.** A `Duration` cannot be accidentally passed where a `Timestamp` is expected.
- **Validation is consistent.** Negative `Duration` is rejected everywhere.
- **Documentation lives with the code.** JSDoc on `BreathPhase` is the same docs seen by mobile and backend.
- **Tests run once.** 299 tests in shared-contracts catch breakage across both targets.
- **New engines ship faster.** Protocol Engine (Sprint 3) needs only to implement interfaces; types come for free.

### Negative

- **Adding a primitive is heavyweight.** Branded type + constructor + JSDoc + tests + version bump. Intentionally slow.
- **Cross-package refactors require coordination.** A change to `BreathPhase` is typechecked in both `mobile/` and `backend/` immediately.
- **Strict mode is contagious.** New packages must adopt strict TS to consume the contracts cleanly.

### Neutral

- The `BreathPhase` value naming (`'inhaling'`) differs from the JSON serialization schema (`'inhale'`). The schema in `protocol/index.ts` is for IPC; the enum here is for runtime engines. Both are intentional and documented.

## Alternatives Considered

### Alternative A: No shared package, copy types between targets

Rejected: drift inevitable, validation diverged even in Sprint 2.

### Alternative B: shared-contracts as runtime dependency (zod schemas exported)

Rejected: too heavy for mobile bundle; types alone are sufficient since engines are pure TS. Schemas are used only at API boundaries.

### Alternative C: Generate types from a single `.proto` or `.json` file

Rejected: adds build-time tooling; over-engineered for a project of this size; types are human-authored and reviewed.

### Alternative D: Use existing library (io-ts, zod) for everything

Rejected: zod is already used for API DTOs, but branded primitives + Result patterns need a hand-crafted layer for ergonomics and zero-dep purity.

## Compliance

This ADR is enforced by:

- `shared-contracts/jest.config.js` thresholds: 100% on every metric.
- TypeScript strict mode at the monorepo root (`tsconfig.base.json`).
- ESLint rules forbidding `any` in shared files.
- Code review: any PR adding a type to `mobile/` or `backend/` that overlaps with shared-contracts is rejected.

## References

- `docs/AraFlow/37_CORE_CONTRACTS.md` — User-facing reference
- `docs/AraFlow/37_SPRINT2_5_REPORT.md` — Sprint 2.5 outcomes
- `docs/adr/araflow/017-typescript-strict-branded.md` — Predecessor ADR
- `docs/adr/araflow/019-master-clock-implementation.md` — Engine contract foundation
