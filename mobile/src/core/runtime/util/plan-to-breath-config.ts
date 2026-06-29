/**
 * plan-to-breath-config — derives a BreathCycleConfig (4-phase) from a
 * N-phase ProtocolExecutionPlan.
 *
 * Moved from `tools/araflow-cli/src/util/breath-config.ts` (Sprint 3.5)
 * into Core as part of Sprint 4 — it's the canonical mapping for
 * integrating ProtocolRuntime plans into the rigid 4-phase Breath Engine.
 *
 * The Breath Engine's lifecycle is rigid: inhale → hold-inhale → exhale →
 * hold-exhale, repeated `cycles` times. A ProtocolExecutionPlan can have
 * N phases (e.g. box breathing has 4 phases per cycle; physiological
 * sigh has 3).
 *
 * Strategy:
 *   - Walk the plan's first cycle's phases.
 *   - Pick the FIRST inhale phase as `inhaleMs`.
 *   - Pick the FIRST hold-in phase as `holdAfterInhaleMs`.
 *   - Pick the FIRST exhale phase as `exhaleMs`.
 *   - Pick the FIRST hold-out phase as `holdAfterExhaleMs`.
 *   - If a phase type is absent, use 0ms.
 *
 * Intentionally lossy — Breath Engine is a side-channel observer
 * during a `run` session, not the source of truth. ProtocolRuntime owns
 * the canonical timeline.
 */

import type { BreathCycleConfig } from '@core/breath-engine';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

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
        if (inhaleMs === 0) {
          inhaleMs = durationMs(phase);
        }
        break;
      case 'holdAfterInhale':
        if (holdAfterInhaleMs === 0) {
          holdAfterInhaleMs = durationMs(phase);
        }
        break;
      case 'exhaling':
        if (exhaleMs === 0) {
          exhaleMs = durationMs(phase);
        }
        break;
      case 'holdAfterExhale':
        if (holdAfterExhaleMs === 0) {
          holdAfterExhaleMs = durationMs(phase);
        }
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
