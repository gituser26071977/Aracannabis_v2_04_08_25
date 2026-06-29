/**
 * planToBreathConfig utility tests — re-exported from @core/runtime.
 * These tests live here as integration coverage for the CLI re-export.
 */

import { planToBreathConfig } from '@core/runtime';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import { Duration } from '@araflow/shared-contracts';

const buildPlan = (
  cycles: number,
  phaseMap: Array<{
    phase: 'inhaling' | 'holdAfterInhale' | 'exhaling' | 'holdAfterExhale';
    ms: number;
  }>,
): ProtocolExecutionPlan => {
  const phasesPerCycle = phaseMap.length;
  const total = cycles * phasesPerCycle;
  const phases = [];
  for (let i = 0; i < total; i += 1) {
    const idxInCycle = i % phasesPerCycle;
    const tpl = phaseMap[idxInCycle]!;
    phases.push({
      index: i as never,
      phase: tpl.phase,
      duration: Duration(tpl.ms),
      curve: 'linear' as const,
    });
  }
  const cycleMs = phaseMap.reduce((a, p) => a + p.ms, 0);
  return {
    executionId: 'exec-1' as never,
    protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FAV' as never,
    version: '1.0.0' as never,
    schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
    compilerVersion: '1.0.0',
    title: 'T',
    metadata: { references: [], contraindications: [], tags: [] },
    phases,
    cycles,
    totalDuration: Duration(cycleMs * cycles),
    totalCycleDuration: Duration(cycleMs),
    compiledAt: '2026-01-01T00:00:00.000Z' as never,
    compiledBy: 'cli-harness' as never,
    checksum: 'fnv1a:abcd',
  };
};

describe('planToBreathConfig', () => {
  it('maps a 4-phase box pattern correctly', () => {
    const plan = buildPlan(3, [
      { phase: 'inhaling', ms: 4000 },
      { phase: 'holdAfterInhale', ms: 4000 },
      { phase: 'exhaling', ms: 4000 },
      { phase: 'holdAfterExhale', ms: 4000 },
    ]);
    const cfg = planToBreathConfig(plan);
    expect(cfg.inhaleMs).toBe(4000);
    expect(cfg.holdAfterInhaleMs).toBe(4000);
    expect(cfg.exhaleMs).toBe(4000);
    expect(cfg.holdAfterExhaleMs).toBe(4000);
    expect(cfg.cycles).toBe(3);
  });

  it('uses 0 for absent phase types', () => {
    const plan = buildPlan(2, [
      { phase: 'inhaling', ms: 4000 },
      { phase: 'exhaling', ms: 4000 },
    ]);
    const cfg = planToBreathConfig(plan);
    expect(cfg.inhaleMs).toBe(4000);
    expect(cfg.exhaleMs).toBe(4000);
    expect(cfg.holdAfterInhaleMs).toBe(0);
    expect(cfg.holdAfterExhaleMs).toBe(0);
  });

  it('clamps zero inhale/exhale to minimum 1', () => {
    // Pathological plan: no inhale or exhale (only holds). Should clamp to 1.
    const plan = buildPlan(1, [
      { phase: 'holdAfterInhale', ms: 1000 },
      { phase: 'holdAfterExhale', ms: 1000 },
    ]);
    const cfg = planToBreathConfig(plan);
    expect(cfg.inhaleMs).toBe(1);
    expect(cfg.exhaleMs).toBe(1);
  });

  it('preserves cycles count', () => {
    const plan = buildPlan(10, [
      { phase: 'inhaling', ms: 4000 },
      { phase: 'exhaling', ms: 4000 },
    ]);
    const cfg = planToBreathConfig(plan);
    expect(cfg.cycles).toBe(10);
  });

  it('only inspects the first cycle', () => {
    // 5 cycles × 2 phases = 10 phases total
    // Make first cycle inhale 2s, second cycle inhale 5s — should pick 2s.
    const plan = buildPlan(5, [
      { phase: 'inhaling', ms: 2000 },
      { phase: 'exhaling', ms: 4000 },
    ]);
    const cfg = planToBreathConfig(plan);
    expect(cfg.inhaleMs).toBe(2000);
  });

  it('ignores unknown phase types (defensive default branch)', () => {
    // Cast through unknown to bypass the strict BreathPhaseType union and
    // exercise the `default: break;` defensive branch.
    const plan = buildPlan(2, [
      { phase: 'inhaling', ms: 4000 },
      { phase: 'exhaling', ms: 4000 },
    ]);
    (plan.phases[0] as unknown as { phase: string }).phase = 'mystery-phase';
    const cfg = planToBreathConfig(plan);
    // Unknown phase does not contribute to the breath config.
    expect(cfg.inhaleMs).toBe(1); // clamped from 0
    expect(cfg.exhaleMs).toBe(4000);
  });
});
