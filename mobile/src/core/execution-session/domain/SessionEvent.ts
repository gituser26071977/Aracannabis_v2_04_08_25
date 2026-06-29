/**
 * SessionEvent — tagged-union of every domain event an Aggregate
 * emits during its lifecycle.
 *
 * The event log is the canonical audit trail of a session. The
 * session state can always be reconstructed from a log replay, and
 * every transition must produce exactly one event.
 *
 * All events carry `monotonicMs` so downstream projections (metrics,
 * timeline, snapshots) can be ordered deterministically.
 */

import type { BreathPhase, ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { SessionState } from './SessionState';

/**
 * ExecutionPlanId — opaque identifier of a compiled execution plan.
 *
 * Re-exposed here so the session domain doesn't import the compiler
 * internal type. The session only needs the *opaque identifier*; it
 * never inspects the plan content beyond what was injected at
 * construction time.
 */
export type ExecutionPlanId = string & { readonly __executionPlanId: unique symbol };

export const ExecutionPlanId = (raw: string): ExecutionPlanId => raw as ExecutionPlanId;

// =============================================================================
// Lifecycle events
// =============================================================================

export interface SessionCreatedEvent {
  readonly type: 'session-created';
  readonly sessionId: SessionId;
  readonly protocolId: ProtocolId;
  readonly executionPlanId: ExecutionPlanId;
  readonly state: SessionState;
  readonly monotonicMs: number;
}

export interface SessionStartedEvent {
  readonly type: 'session-started';
  readonly monotonicMs: number;
}

export interface SessionPreparingEvent {
  readonly type: 'session-preparing';
  readonly monotonicMs: number;
}

export interface SessionPausedEvent {
  readonly type: 'session-paused';
  readonly monotonicMs: number;
  readonly pausedForMs: number;
}

export interface SessionResumedEvent {
  readonly type: 'session-resumed';
  readonly monotonicMs: number;
  readonly resumedFromMs: number;
}

export interface SessionCancelledEvent {
  readonly type: 'session-cancelled';
  readonly monotonicMs: number;
  readonly reason: string;
}

export interface SessionCompletedEvent {
  readonly type: 'session-completed';
  readonly monotonicMs: number;
  readonly totalElapsedMs: number;
}

export interface SessionFailedEvent {
  readonly type: 'session-failed';
  readonly monotonicMs: number;
  readonly code: string;
  readonly message: string;
}

export interface SessionInterruptedEvent {
  readonly type: 'session-interrupted';
  readonly monotonicMs: number;
  readonly reason: string;
}

// =============================================================================
// Observation events
// =============================================================================

export interface PhaseChangedEvent {
  readonly type: 'phase-changed';
  readonly monotonicMs: number;
  readonly phase: BreathPhase;
  readonly cycleIndex: number;
  readonly phaseIndex: number;
  readonly phaseElapsedMs: number;
  readonly phaseDurationMs: number;
}

export interface CycleCompletedEvent {
  readonly type: 'cycle-completed';
  readonly monotonicMs: number;
  readonly cycleIndex: number;
  readonly cycleElapsedMs: number;
  readonly totalCycles: number;
}

export interface MetricUpdatedEvent {
  readonly type: 'metric-updated';
  readonly monotonicMs: number;
  readonly metric: string;
  readonly value: number;
}

export interface SnapshotCreatedEvent {
  readonly type: 'snapshot-created';
  readonly monotonicMs: number;
  readonly version: number;
}

// =============================================================================
// Tagged union
// =============================================================================

export type SessionEvent =
  | SessionCreatedEvent
  | SessionPreparingEvent
  | SessionStartedEvent
  | SessionPausedEvent
  | SessionResumedEvent
  | SessionCancelledEvent
  | SessionCompletedEvent
  | SessionFailedEvent
  | SessionInterruptedEvent
  | PhaseChangedEvent
  | CycleCompletedEvent
  | MetricUpdatedEvent
  | SnapshotCreatedEvent;

export const SESSION_EVENT_TYPES: readonly SessionEvent['type'][] = [
  'session-created',
  'session-preparing',
  'session-started',
  'session-paused',
  'session-resumed',
  'session-cancelled',
  'session-completed',
  'session-failed',
  'session-interrupted',
  'phase-changed',
  'cycle-completed',
  'metric-updated',
  'snapshot-created',
] as const;

export const isSessionEvent = (v: unknown): v is SessionEvent => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const t = (v as { type?: unknown }).type;
  return typeof t === 'string' && (SESSION_EVENT_TYPES as readonly string[]).includes(t);
};

export const isSessionLifecycleEventType = (
  t: string,
): t is
  | 'session-created'
  | 'session-preparing'
  | 'session-started'
  | 'session-paused'
  | 'session-resumed'
  | 'session-cancelled'
  | 'session-completed'
  | 'session-failed'
  | 'session-interrupted' =>
  (
    [
      'session-created',
      'session-preparing',
      'session-started',
      'session-paused',
      'session-resumed',
      'session-cancelled',
      'session-completed',
      'session-failed',
      'session-interrupted',
    ] as readonly string[]
  ).includes(t);
