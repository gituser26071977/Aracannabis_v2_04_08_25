/**
 * BreathEngine — real-time benchmark.
 *
 * Runs a 30-second session using real setTimeout to measure production
 * behavior. Validates that the default infrastructure path works under
 * real-time conditions.
 *
 * Run with: npx ts-node mobile/__tests__/core/breath-engine/BreathEngine.bench.run.ts
 * Or: npx jest --testPathPattern BreathEngine.bench.run
 */

import {
  BreathEngine,
  type BreathCycleConfig,
} from '@core/breath-engine';

import { createTimerEngine } from '@core/timer-engine';
import { createBrowserMonotonicClock } from '@core/timer-engine';

const FAST_CONFIG: BreathCycleConfig = {
  inhaleMs: 1_500,
  holdAfterInhaleMs: 500,
  exhaleMs: 1_500,
  holdAfterExhaleMs: 500,
  cycles: 10,
};

const SESSION_DURATION_MS = 30_000;

describe('BreathEngine — real-time 30s benchmark', () => {
  it('runs 30s real-time breath session and reports metrics', (done) => {
    const monotonic = createBrowserMonotonicClock();
    const timer = createTimerEngine();
    timer.start();
    const breath = new BreathEngine({
      monotonic,
      timerEngine: timer,
      config: FAST_CONFIG,
    });

    let phaseChanges = 0;
    let cycleStarts = 0;
    breath.subscribe((e) => {
      if (e.type === 'phase-changed') phaseChanges += 1;
      if (e.type === 'cycle-started') cycleStarts += 1;
    });

    breath.start();

    setTimeout(() => {
      breath.cancel();
      breath.dispose();

      // eslint-disable-next-line no-console
      console.log(`
[BENCH — Real Time Breath]
  Session target:    ${SESSION_DURATION_MS}ms
  Cycles configured: ${FAST_CONFIG.cycles}
  Cycle duration:    ${(FAST_CONFIG.inhaleMs + FAST_CONFIG.holdAfterInhaleMs + FAST_CONFIG.exhaleMs + FAST_CONFIG.holdAfterExhaleMs)}ms
  Phase changes:     ${phaseChanges}
  Cycle starts:      ${cycleStarts}
`);

      expect(phaseChanges).toBeGreaterThan(0);
      done();
    }, SESSION_DURATION_MS);
  }, 35000);
});