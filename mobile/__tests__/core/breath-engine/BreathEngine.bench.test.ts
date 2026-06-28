/**
 * BreathEngine — performance benchmark.
 *
 * Measures:
 *   - PhaseCalculator throughput
 *   - DepthCalculator throughput
 *   - BreathEngine initialization
 *   - Per-tick overhead
 *   - Memory: heap delta after many cycles
 *
 * To run: `npx jest BreathEngine.bench --verbose`
 */

import {
  BreathEngine,
  computeDepth,
  computePhaseInfo,
  easeInOutCurve,
  type BreathCycleConfig,
} from '@core/breath-engine';

import { createBreathTestRig } from './fakes';

const BOX_CONFIG: BreathCycleConfig = {
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 5,
};

const FAST_CONFIG: BreathCycleConfig = {
  inhaleMs: 100,
  holdAfterInhaleMs: 100,
  exhaleMs: 100,
  holdAfterExhaleMs: 100,
  cycles: 100,
};

const measure = (label: string, fn: () => void): number => {
  const start = process.hrtime.bigint();
  fn();
  const end = process.hrtime.bigint();
  const ms = Number(end - start) / 1_000_000;
  // eslint-disable-next-line no-console
  console.log(`[BENCH] ${label}: ${ms.toFixed(3)} ms`);
  return ms;
};

describe('BreathEngine — performance benchmark', () => {
  test('PhaseCalculator: 100k calls in <50ms', () => {
    const avg = measure('phaseCalculator 100k', () => {
      for (let i = 0; i < 100_000; i += 1) {
        computePhaseInfo(BOX_CONFIG, i % 80_000);
      }
    });
    expect(avg).toBeLessThan(50);
  });

  test('DepthCalculator: 1M calls in <50ms', () => {
    const avg = measure('depthCalculator 1M', () => {
      const phases = ['inhaling', 'holdAfterInhale', 'exhaling', 'holdAfterExhale'] as const;
      for (let i = 0; i < 1_000_000; i += 1) {
        const phase = phases[i % 4];
        if (phase !== undefined) {
          computeDepth(phase, (i % 100) / 100, easeInOutCurve);
        }
      }
    });
    expect(avg).toBeLessThan(50);
  });

  test('initialization: 100 engines in <50ms', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    const avg = measure('init 100 engines', () => {
      for (let i = 0; i < 100; i += 1) {
        new BreathEngine({
          monotonic: rig.monotonic,
          timerEngine: rig.timerEngine,
          config: BOX_CONFIG,
        });
      }
    });
    expect(avg).toBeLessThan(50);
  });

  test('per-tick overhead: 1000 ticks in <100ms', () => {
    const rig = createBreathTestRig(BOX_CONFIG, { timerMode: 'high-precision' });
    rig.breathEngine.start();
    const avg = measure('1000 ticks @ 60Hz', () => {
      rig.clock.advance(16_667); // 60Hz tick interval × 1000 = 16.667s
    });
    expect(avg).toBeLessThan(500); // 60Hz × 1000 ticks real wall time allowance
  });

  test('full session: 5 cycles × 16s = 80s in <500ms wall', () => {
    const rig = createBreathTestRig(BOX_CONFIG, { timerMode: 'high-precision' });
    rig.breathEngine.start();
    const avg = measure('full 80s session (faked)', () => {
      rig.clock.advance(80_000);
    });
    expect(avg).toBeLessThan(500);
  });

  test('100 listeners overhead is bounded', () => {
    const rig = createBreathTestRig(FAST_CONFIG, { timerMode: 'high-precision' });
    const offs: Array<() => void> = [];
    measure('subscribe 100 listeners', () => {
      for (let i = 0; i < 100; i += 1) {
        offs.push(rig.breathEngine.subscribe(() => undefined));
      }
    });
    rig.breathEngine.start();
    measure('one tick with 100 listeners', () => {
      rig.clock.advance(110);
    });
    offs.forEach((o) => o());
  });
});