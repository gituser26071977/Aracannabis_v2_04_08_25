/**
 * session-metrics — pure projection from event log to SessionMetrics.
 *
 * Given an immutable event log and the planned total duration, this
 * module derives every numeric field of SessionMetrics. Pure function;
 * no side effects; no clock access (caller passes `nowMs`).
 */

import type { BreathPhase } from '@araflow/shared-contracts';

import type { SessionEvent } from '../domain/SessionEvent';
import { EMPTY_SESSION_METRICS, type SessionMetrics } from '../domain/SessionMetrics';

export interface ComputeMetricsInput {
  readonly events: readonly SessionEvent[];
  readonly plannedDurationMs: number;
  readonly nowMs: number;
}

const safeElapsed = (sessionStartMs: number | null, end: number): number =>
  sessionStartMs === null ? 0 : Math.max(0, end - sessionStartMs);

export const computeMetrics = (input: ComputeMetricsInput): SessionMetrics => {
  const { events, plannedDurationMs, nowMs } = input;
  if (events.length === 0) {
    return Object.freeze({
      ...EMPTY_SESSION_METRICS,
      remainingMs: plannedDurationMs,
    });
  }

  let sessionStartMs: number | null = null;
  let sessionEndMs: number | null = null;
  let pauseCount = 0;
  let pauseDurationMs = 0;
  let lastPauseStartMs: number | null = null;
  let completedCycles = 0;
  let currentCycle = 0;
  let currentPhase: BreathPhase | null = null;

  for (const ev of events) {
    switch (ev.type) {
      case 'session-started':
        sessionStartMs = ev.monotonicMs;
        break;
      case 'session-completed':
      case 'session-cancelled':
      case 'session-failed':
      case 'session-interrupted':
        sessionEndMs = ev.monotonicMs;
        break;
      case 'session-paused':
        pauseCount += 1;
        lastPauseStartMs = ev.monotonicMs;
        break;
      case 'session-resumed':
        if (lastPauseStartMs !== null) {
          pauseDurationMs += ev.monotonicMs - lastPauseStartMs;
          lastPauseStartMs = null;
        }
        break;
      case 'phase-changed':
        currentPhase = ev.phase;
        currentCycle = ev.cycleIndex;
        break;
      case 'cycle-completed':
        completedCycles += 1;
        break;
      default:
        break;
    }
  }

  const effectiveNow = sessionEndMs ?? nowMs;
  const sessionDurationMs = safeElapsed(sessionStartMs, effectiveNow);
  const elapsedMs = sessionStartMs === null ? 0 : Math.max(0, sessionDurationMs - pauseDurationMs);
  const remainingMs =
    sessionStartMs === null ? plannedDurationMs : Math.max(0, plannedDurationMs - elapsedMs);
  const progress =
    plannedDurationMs <= 0 ? 0 : Math.max(0, Math.min(1, elapsedMs / plannedDurationMs));

  // Adjust completed cycles if currentCycle > completedCycles (mid-cycle).
  const reportedCurrentCycle = Math.max(currentCycle, completedCycles);

  return Object.freeze({
    elapsedMs,
    remainingMs,
    completedCycles,
    currentCycle: reportedCurrentCycle,
    currentPhase,
    progress,
    pauseCount,
    pauseDurationMs,
    sessionDurationMs,
  });
};
