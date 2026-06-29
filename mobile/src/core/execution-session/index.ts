/**
 * @core/execution-session — Execution Session Aggregate Root.
 *
 * The single source of truth of a breathing session. Owns identity,
 * FSM, event log, metrics, timeline, and snapshot. The Aggregate is
 * a pure domain model — no persistence, no UI, no React, no network.
 *
 * Version: 1.0.0 — frozen upon completion of Sprint 5.
 *
 * Consumers must NOT import any internal module directly. Always
 * import from this barrel.
 */

export { ExecutionSession } from './application/ExecutionSession';
export type { ExecutionSessionDeps, MonotonicClock } from './application/ExecutionSessionDeps';

// --- Domain types ---
export {
  type SessionState,
  SESSION_STATES,
  TERMINAL_SESSION_STATES,
  ACTIVE_SESSION_STATES,
  isSessionState,
  isTerminalSessionState,
  isActiveSessionState,
  legalTransitions,
  canTransition,
} from './domain/SessionState';
export {
  ExecutionPlanId,
  type SessionEvent,
  SESSION_EVENT_TYPES,
  isSessionEvent,
  isSessionLifecycleEventType,
  type SessionCreatedEvent,
  type SessionPreparingEvent,
  type SessionStartedEvent,
  type SessionPausedEvent,
  type SessionResumedEvent,
  type SessionCancelledEvent,
  type SessionCompletedEvent,
  type SessionFailedEvent,
  type SessionInterruptedEvent,
  type PhaseChangedEvent,
  type CycleCompletedEvent,
  type MetricUpdatedEvent,
  type SnapshotCreatedEvent,
} from './domain/SessionEvent';
export { type SessionMetrics, EMPTY_SESSION_METRICS } from './domain/SessionMetrics';
export type { SessionSnapshot } from './domain/SessionSnapshot';
export {
  type SessionTimeline,
  type SessionTimelineEntry,
  type SessionTimelineKind,
} from './domain/SessionTimeline';

// --- Utilities (re-exported from util/) ---
export { computeMetrics, type ComputeMetricsInput } from './util/session-metrics';
export { buildTimeline } from './util/session-timeline';

// --- Version ---
export const EXECUTION_SESSION_VERSION = '1.0.0' as const;
