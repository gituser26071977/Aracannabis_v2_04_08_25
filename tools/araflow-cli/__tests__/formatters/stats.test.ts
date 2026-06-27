/**
 * stats formatter tests.
 */

import { computeStats, formatStats } from '../../src/formatters/stats';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import { Duration } from '@araflow/shared-contracts';

const fakePlan = (
  cycles: number,
  phasesPerCycle: number,
  phaseMs: number,
): ProtocolExecutionPlan => {
  const phases = [];
  for (let i = 0; i < cycles * phasesPerCycle; i += 1) {
    phases.push({
      index: i as never,
      phase: 'inhaling' as const,
      duration: Duration(phaseMs),
      curve: 'linear' as const,
    });
  }
  return {
    executionId: 'exec-1' as never,
    protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FAV' as never,
    version: '1.0.0' as never,
    schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
    compilerVersion: '1.0.0',
    title: 'Test',
    metadata: {
      references: [],
      contraindications: [],
      tags: [],
    },
    phases,
    cycles,
    totalDuration: Duration(cycles * phasesPerCycle * phaseMs),
    totalCycleDuration: Duration(phasesPerCycle * phaseMs),
    compiledAt: '2026-01-01T00:00:00.000Z' as never,
    compiledBy: 'cli-harness' as never,
    checksum: 'fnv1a:abcd1234',
  };
};

describe('computeStats', () => {
  it('counts cycles and phases', () => {
    const s = computeStats(fakePlan(4, 3, 1000));
    expect(s.cycles).toBe(4);
    expect(s.totalPhases).toBe(12);
    expect(s.phasesPerCycle).toBe(3);
  });

  it('computes totalDurationMs and sec', () => {
    const s = computeStats(fakePlan(2, 2, 1000));
    expect(s.totalDurationMs).toBe(4000);
    expect(s.totalDurationSec).toBe(4);
  });

  it('computes avg phase duration', () => {
    const s = computeStats(fakePlan(3, 2, 1500));
    expect(s.avgPhaseMs).toBe(1500);
    expect(s.avgPhaseSec).toBe(1.5);
  });

  it('computes breaths per minute', () => {
    // 4 cycles in 60 seconds → 4 BPM
    const s = computeStats(fakePlan(4, 3, 5000));
    expect(s.breathsPerMinute).toBeCloseTo(4, 1);
  });

  it('builds phases breakdown', () => {
    const plan = fakePlan(2, 1, 1000);
    plan.phases[0] = { ...plan.phases[0]!, phase: 'inhaling' };
    plan.phases[1] = { ...plan.phases[1]!, phase: 'exhaling' };
    const s = computeStats(plan);
    expect(s.phasesBreakdown['inhaling']).toBe(1);
    expect(s.phasesBreakdown['exhaling']).toBe(1);
  });

  it('returns 0 for empty plan', () => {
    const empty = fakePlan(0, 0, 0);
    const s = computeStats(empty);
    expect(s.totalPhases).toBe(0);
    expect(s.avgPhaseMs).toBe(0);
  });
});

describe('formatStats', () => {
  it('renders all sections', () => {
    const s = computeStats(fakePlan(2, 2, 1000));
    const out = formatStats(s);
    expect(out).toContain('Statistics');
    expect(out).toContain('cycles');
    expect(out).toContain('total duration');
    expect(out).toContain('phases breakdown');
  });
});
