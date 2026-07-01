/**
 * InconsistencyReport — typed surface of every inconsistency the
 * Orchestrator detects between the Runtime and the Session.
 *
 * Detected categories:
 *   - 'out-of-order'    — Runtime event timestamp is older than the
 *                         last event the Session has seen.
 *   - 'impossible-state'— Runtime event requires a Session state that
 *                         does not legally produce it.
 *   - 'invalid-cycle'   — Runtime event has a cycleIndex that the
 *                         Session's plan does not contain.
 *   - 'invalid-phase'   — Runtime event has a phase that the Session's
 *                         plan does not contain.
 *   - 'divergence'      — Runtime and Session report incompatible
 *                         states for the same logical lifecycle point.
 *
 * Reports are append-only (Object.freeze). Once emitted they are
 * never mutated; further detections create additional reports.
 */

import type { SessionState } from '@core/execution-session';
import type { RuntimeState } from '@core/runtime';

export type InconsistencyKind =
  | 'out-of-order'
  | 'impossible-state'
  | 'invalid-cycle'
  | 'invalid-phase'
  | 'divergence';

export const INCONSISTENCY_KINDS: readonly InconsistencyKind[] = [
  'out-of-order',
  'impossible-state',
  'invalid-cycle',
  'invalid-phase',
  'divergence',
] as const;

export const isInconsistencyKind = (value: unknown): value is InconsistencyKind =>
  typeof value === 'string' && (INCONSISTENCY_KINDS as readonly string[]).includes(value);

export interface InconsistencyReport {
  readonly kind: InconsistencyKind;
  readonly code: string;
  readonly message: string;
  readonly monotonicMs: number;
  readonly context: Readonly<Record<string, unknown>>;
}

export const EMPTY_INCONSISTENCY_REPORTS: readonly InconsistencyReport[] = Object.freeze([]);

export const freezeInconsistency = (report: InconsistencyReport): InconsistencyReport =>
  Object.freeze(report);

// =============================================================================
// Constructor helpers (typed factories)
// =============================================================================

export const outOfOrderReport = (input: {
  readonly monotonicMs: number;
  readonly eventMonotonicMs: number;
  readonly eventType: string;
}): InconsistencyReport =>
  Object.freeze({
    kind: 'out-of-order',
    code: 'orchestrator_out_of_order',
    message: 'Runtime event arrived after newer events have already been processed',
    monotonicMs: input.monotonicMs,
    context: Object.freeze({
      eventType: input.eventType,
      eventMonotonicMs: input.eventMonotonicMs,
    }),
  });

export const impossibleStateReport = (input: {
  readonly monotonicMs: number;
  readonly eventType: string;
  readonly sessionState: SessionState;
}): InconsistencyReport =>
  Object.freeze({
    kind: 'impossible-state',
    code: 'orchestrator_impossible_state',
    message: 'Runtime event requires a Session state that cannot produce it',
    monotonicMs: input.monotonicMs,
    context: Object.freeze({
      eventType: input.eventType,
      sessionState: input.sessionState,
    }),
  });

export const invalidCycleReport = (input: {
  readonly monotonicMs: number;
  readonly cycleIndex: number;
  readonly totalCycles: number;
}): InconsistencyReport =>
  Object.freeze({
    kind: 'invalid-cycle',
    code: 'orchestrator_invalid_cycle',
    message: "Runtime event references a cycle outside the Session's plan",
    monotonicMs: input.monotonicMs,
    context: Object.freeze({
      cycleIndex: input.cycleIndex,
      totalCycles: input.totalCycles,
    }),
  });

export const invalidPhaseReport = (input: {
  readonly monotonicMs: number;
  readonly phase: string;
}): InconsistencyReport =>
  Object.freeze({
    kind: 'invalid-phase',
    code: 'orchestrator_invalid_phase',
    message: "Runtime event references a phase outside the Session's plan",
    monotonicMs: input.monotonicMs,
    context: Object.freeze({ phase: input.phase }),
  });

export const divergenceReport = (input: {
  readonly monotonicMs: number;
  readonly runtimeState: RuntimeState;
  readonly sessionState: SessionState;
}): InconsistencyReport =>
  Object.freeze({
    kind: 'divergence',
    code: 'orchestrator_divergence',
    message: 'Runtime and Session states are incompatible at this point',
    monotonicMs: input.monotonicMs,
    context: Object.freeze({
      runtimeState: input.runtimeState,
      sessionState: input.sessionState,
    }),
  });
