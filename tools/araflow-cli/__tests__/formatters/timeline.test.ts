/**
 * timeline formatter tests.
 */

import { formatSimulationTimeline, formatRuntimeEventStream } from '../../src/formatters/timeline';
import type { SimulationPhaseRecord, SimulationCycleRecord } from '@core/protocol-compiler';

describe('formatSimulationTimeline', () => {
  it('renders header', () => {
    const out = formatSimulationTimeline([], []);
    expect(out).toContain('Timeline (Simulation)');
  });

  it('renders phases', () => {
    const phases: SimulationPhaseRecord[] = [
      {
        cycleIndex: 0,
        phaseIndex: 0,
        phase: 'inhaling',
        durationMs: 4000,
        startedAtMs: 0,
        endedAtMs: 4000,
      },
      {
        cycleIndex: 0,
        phaseIndex: 1,
        phase: 'exhaling',
        durationMs: 4000,
        startedAtMs: 4000,
        endedAtMs: 8000,
      },
    ];
    const out = formatSimulationTimeline(phases, []);
    expect(out).toContain('inhaling');
    expect(out).toContain('exhaling');
    expect(out).toContain('4.00s');
  });

  it('renders cycles summary', () => {
    const cycles: SimulationCycleRecord[] = [
      {
        cycleIndex: 0,
        phases: [],
        cycleDurationMs: 8000,
      },
      {
        cycleIndex: 1,
        phases: [],
        cycleDurationMs: 8000,
      },
    ];
    const out = formatSimulationTimeline([], cycles);
    expect(out).toContain('Cycles (2)');
    expect(out).toMatch(/cycle\s+0/);
    expect(out).toMatch(/cycle\s+1/);
  });
});

describe('formatRuntimeEventStream', () => {
  it('renders header', () => {
    const out = formatRuntimeEventStream([]);
    expect(out).toContain('Runtime Event Stream');
  });

  it('tags events by stream', () => {
    const out = formatRuntimeEventStream([
      { t: 0, stream: 'protocol', summary: 'started' },
      { t: 100, stream: 'breath', summary: 'phase=inhaling' },
      { t: 200, stream: 'timer', summary: 'timer tick' },
    ]);
    expect(out).toContain('[protocol]');
    expect(out).toContain('[breath]');
    expect(out).toContain('[timer]');
    expect(out).toContain('started');
  });
});
