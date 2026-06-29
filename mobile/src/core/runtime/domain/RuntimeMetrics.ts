/**
 * RuntimeMetrics — aggregated metrics derived from engine events.
 *
 * `aggregateMetrics(snapshot, plan, counters)` is a pure function
 * called on every RuntimeEvent so the public `getMetrics()` is O(1).
 * The counters are kept on the Runtime instance and updated by the
 * event bridge.
 */

import type { BreathPhase } from '@araflow/shared-contracts';

export interface EventCounters {
  readonly timer: number;
  readonly breath: number;
  readonly protocol: number;
  readonly runtime: number;
}

export interface RuntimeMetrics {
  readonly elapsedMs: number;
  readonly plannedDurationMs: number;
  readonly driftMs: number;
  readonly cyclesCompleted: number;
  readonly totalCycles: number;
  readonly currentCycle: number;
  readonly currentPhase: BreathPhase | null;
  readonly phaseProgress: number;
  readonly tickCount: number;
  readonly pauseCount: number;
  readonly totalPausedMs: number;
  readonly warnings: number;
  readonly errors: number;
  readonly eventCounters: EventCounters;
}
