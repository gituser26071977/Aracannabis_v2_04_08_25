/**
 * SessionMetrics — derived read model of a session.
 *
 * Computed from the event log (pure projection). Never mutated in place;
 * any change produces a new object via the Aggregate.
 */

import type { BreathPhase } from '@araflow/shared-contracts';

export interface SessionMetrics {
  readonly elapsedMs: number;
  readonly remainingMs: number;
  readonly completedCycles: number;
  readonly currentCycle: number;
  readonly currentPhase: BreathPhase | null;
  readonly progress: number;
  readonly pauseCount: number;
  readonly pauseDurationMs: number;
  readonly sessionDurationMs: number;
}

export const EMPTY_SESSION_METRICS: SessionMetrics = Object.freeze({
  elapsedMs: 0,
  remainingMs: 0,
  completedCycles: 0,
  currentCycle: 0,
  currentPhase: null,
  progress: 0,
  pauseCount: 0,
  pauseDurationMs: 0,
  sessionDurationMs: 0,
});
