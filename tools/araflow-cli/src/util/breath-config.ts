/**
 * breath-config — derives a BreathCycleConfig (4-phase) from a
 * N-phase ProtocolExecutionPlan.
 *
 * The Breath Engine's lifecycle is rigid: inhale → hold-inhale → exhale →
 * hold-exhale, repeated `cycles` times. A ProtocolExecutionPlan can have
 * N phases (e.g. box breathing has 4 phases per cycle).
 *
 * Strategy:
 *   - Walk the plan's first cycle's phases.
 *   - Pick the FIRST inhale phase as `inhaleMs`.
 *   - Pick the FIRST hold-in phase as `holdAfterInhaleMs`.
 *   - Pick the FIRST exhale phase as `exhaleMs`.
 *   - Pick the FIRST hold-out phase as `holdAfterExhaleMs`.
 *   - If a phase type is absent, use 0ms.
 *
 * This is intentionally lossy — Breath Engine is a side-channel observer
 * during a `run` command, not the source of truth. ProtocolRuntime owns
 * the canonical timeline.
 */

import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import type { BreathCycleConfig } from '@core/breath-engine';

const durationMs = (step: { duration: unknown }): number => step.duration as unknown as number;

export const planToBreathConfig = (plan: ProtocolExecutionPlan): BreathCycleConfig => {
  // Plan phases are pre-flattened across cycles. Compute phases-per-cycle
  // and grab only the first cycle's phases.
  const phasesPerCycle = plan.cycles > 0 ? plan.phases.length / plan.cycles : plan.phases.length;
  const firstCycleCount = Math.floor(phasesPerCycle);
  const firstCyclePhases = plan.phases.slice(0, firstCycleCount);

  let inhaleMs = 0;
  let holdAfterInhaleMs = 0;
  let exhaleMs = 0;
  let holdAfterExhaleMs = 0;

  for (const phase of firstCyclePhases) {
    switch (phase.phase) {
      case 'inhaling':
        if (inhaleMs === 0) inhaleMs = durationMs(phase);
        break;
      case 'holdAfterInhale':
        if (holdAfterInhaleMs === 0) holdAfterInhaleMs = durationMs(phase);
        break;
      case 'exhaling':
        if (exhaleMs === 0) exhaleMs = durationMs(phase);
        break;
      case 'holdAfterExhale':
        if (holdAfterExhaleMs === 0) holdAfterExhaleMs = durationMs(phase);
        break;
      default:
        break;
    }
  }

  return {
    inhaleMs: Math.max(1, inhaleMs),
    holdAfterInhaleMs: Math.max(0, holdAfterInhaleMs),
    exhaleMs: Math.max(1, exhaleMs),
    holdAfterExhaleMs: Math.max(0, holdAfterExhaleMs),
    cycles: plan.cycles,
  };
};
