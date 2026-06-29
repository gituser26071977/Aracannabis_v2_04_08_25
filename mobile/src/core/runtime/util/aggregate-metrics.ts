/**
 * aggregate-metrics — pure function: snapshot × plan × counters → RuntimeMetrics.
 *
 * Called on every RuntimeEvent so `getMetrics()` is O(1) read.
 *
 * Idempotent — no counters are mutated here. The Runtime holds the
 * counters (counters are derived from the event stream) and passes
 * them in. This function only DERIVES, never COUNTS.
 */

import type { BreathPhase } from '@araflow/shared-contracts';

import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

import type { EventCounters, RuntimeMetrics } from '../domain/RuntimeMetrics';
import type { RuntimeSnapshot } from '../domain/RuntimeSnapshot';

export interface AggregateMetricsInput {
  readonly snapshot: RuntimeSnapshot;
  readonly plan: ProtocolExecutionPlan | null;
  readonly counters: EventCounters;
  readonly pauseCount: number;
  readonly totalPausedMs: number;
  readonly tickCount: number;
  readonly warnings: number;
  readonly errors: number;
}

export const aggregateMetrics = (input: AggregateMetricsInput): RuntimeMetrics => {
  const { snapshot, plan, counters, pauseCount, totalPausedMs, tickCount, warnings, errors } =
    input;

  const elapsedMs = snapshot.protocol?.elapsedMs ?? 0;
  const plannedDurationMs = plan?.totalDuration ? (plan.totalDuration as unknown as number) : 0;
  const driftMs = elapsedMs - plannedDurationMs;

  const currentPhase: BreathPhase | null = snapshot.protocol?.currentPhase ?? null;
  const phaseProgress = snapshot.protocol?.phaseProgress ?? 0;
  const currentCycle = snapshot.protocol?.cycleIndex ?? 0;
  const totalCycles = plan?.cycles ?? 0;
  const cyclesCompleted =
    snapshot.protocol !== null && snapshot.state === 'completed'
      ? totalCycles
      : Math.max(0, currentCycle);

  return {
    elapsedMs,
    plannedDurationMs,
    driftMs,
    cyclesCompleted,
    totalCycles,
    currentCycle,
    currentPhase,
    phaseProgress,
    tickCount,
    pauseCount,
    totalPausedMs,
    warnings,
    errors,
    eventCounters: counters,
  };
};

export const EMPTY_EVENT_COUNTERS: EventCounters = {
  timer: 0,
  breath: 0,
  protocol: 0,
  runtime: 0,
};
