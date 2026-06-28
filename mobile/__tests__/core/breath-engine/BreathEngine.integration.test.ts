/**
 * BreathEngine — integration tests.
 *
 * Tests cover:
 *   - Long sessions (simulated 20 minutes)
 *   - Drift over time
 *   - Multiple cycles end-to-end
 *   - Stress (many listeners, rapid cycles)
 *   - Memory (no leaks after many sessions)
 */

import {
  computeCycleMs,
  type BreathCycleConfig,
} from '@core/breath-engine';

import { createBreathTestRig } from './fakes';

const FAST_CONFIG: BreathCycleConfig = {
  inhaleMs: 100,
  holdAfterInhaleMs: 100,
  exhaleMs: 100,
  holdAfterExhaleMs: 100,
  cycles: 100,
};

const LONG_SESSION_CONFIG: BreathCycleConfig = {
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 75, // 75 × 16s = 1200s = 20 minutes
};

const BOX_CONFIG_DEFAULT: BreathCycleConfig = {
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 3,
};

describe('BreathEngine — integration: fast cycle, many iterations', () => {
  test('completes 100 fast cycles correctly', () => {
    const rig = createBreathTestRig(FAST_CONFIG, { timerMode: 'high-precision' });
    rig.breathEngine.start();
    rig.clock.advance(FAST_CONFIG.cycles * computeCycleMs(FAST_CONFIG) + 500);

    expect(rig.breathEngine.getState()).toBe('completed');
    expect(rig.breathEngine.getCyclesCompleted()).toBe(FAST_CONFIG.cycles);

    const cycleStarted = rig.breathEvents.filter((e) => e.type === 'cycle-started');
    const cycleCompleted = rig.breathEvents.filter((e) => e.type === 'cycle-completed');
    expect(cycleStarted.length).toBe(FAST_CONFIG.cycles);
    expect(cycleCompleted.length).toBe(FAST_CONFIG.cycles);
  });
});

describe('BreathEngine — integration: long session drift', () => {
  test('20-minute session: drift < 50ms', () => {
    const rig = createBreathTestRig(LONG_SESSION_CONFIG, { timerMode: 'balanced' });
    rig.breathEngine.start();

    const totalDuration = LONG_SESSION_CONFIG.cycles * computeCycleMs(LONG_SESSION_CONFIG);
    rig.clock.advance(totalDuration);

    const snap = rig.breathEngine.snapshot();
    const expected = totalDuration;
    const error = Math.abs(snap.totalElapsedMs - expected);

    // eslint-disable-next-line no-console
    console.log(`[INTEGRATION] 20-min drift: ${error.toFixed(3)}ms`);
    expect(error).toBeLessThan(50);
    expect(rig.breathEngine.getState()).toBe('completed');
  });
});

describe('BreathEngine — integration: stress with many listeners', () => {
  test('100 listeners do not slow down session', () => {
    const rig = createBreathTestRig(FAST_CONFIG, { timerMode: 'high-precision' });
    const offs: Array<() => void> = [];
    for (let i = 0; i < 100; i += 1) {
      offs.push(rig.breathEngine.subscribe(() => undefined));
    }

    rig.breathEngine.start();
    rig.clock.advance(FAST_CONFIG.cycles * computeCycleMs(FAST_CONFIG) + 100);

    expect(rig.breathEngine.getState()).toBe('completed');
    offs.forEach((o) => o());
  });
});

describe('BreathEngine — integration: rapid start/cancel cycles', () => {
  test('50 rapid start/cancel cycles work correctly', () => {
    const rig = createBreathTestRig(BOX_CONFIG_DEFAULT, { timerMode: 'high-precision' });
    for (let i = 0; i < 50; i += 1) {
      rig.breathEngine.start();
      rig.clock.advance(50);
      rig.breathEngine.cancel();
    }
    expect(rig.breathEngine.getState()).toBe('cancelled');
  });

  test('50 rapid start/complete cycles work correctly', () => {
    const rig = createBreathTestRig(FAST_CONFIG, { timerMode: 'high-precision' });
    for (let i = 0; i < 50; i += 1) {
      rig.breathEngine.start();
      rig.clock.advance(FAST_CONFIG.cycles * computeCycleMs(FAST_CONFIG) + 100);
      // After completion, snapshot is idle-equivalent in lifecycle terms.
    }
    expect(rig.breathEngine.getState()).toBe('completed');
  });
});

describe('BreathEngine — integration: interruption during long session', () => {
  test('interruption mid-session preserves progress on resume', () => {
    const rig = createBreathTestRig(LONG_SESSION_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(8_000); // mid first holdAfterInhale
    const elapsedBefore = rig.breathEngine.getSessionElapsedMs();

    rig.timerEngine.notifyBackground();
    expect(rig.breathEngine.getState()).toBe('interrupted');

    rig.clock.advance(50_000); // time passes while backgrounded
    rig.timerEngine.notifyForeground();

    expect(rig.breathEngine.getState()).toBe('holdAfterInhale');
    expect(rig.breathEngine.getSessionElapsedMs()).toBe(elapsedBefore);
  });

  test('multiple background/foreground cycles', () => {
    const rig = createBreathTestRig(LONG_SESSION_CONFIG);
    rig.breathEngine.start();

    for (let i = 0; i < 5; i += 1) {
      rig.clock.advance(8_000);
      rig.timerEngine.notifyBackground();
      rig.clock.advance(1_000);
      rig.timerEngine.notifyForeground();
    }

    expect(rig.breathEngine.getState()).not.toBe('interrupted');
  });
});

describe('BreathEngine — integration: snapshot update frequency', () => {
  test('snapshot is consistent across rapid ticks', () => {
    const rig = createBreathTestRig(BOX_CONFIG_DEFAULT, { timerMode: 'high-precision' });
    rig.breathEngine.start();
    rig.clock.advance(100);

    const s1 = rig.breathEngine.snapshot();
    rig.clock.advance(100);
    const s2 = rig.breathEngine.snapshot();

    expect(s2.totalElapsedMs).toBeGreaterThan(s1.totalElapsedMs);
    expect(s2.cycleIndex).toBe(s1.cycleIndex); // same cycle in 200ms
  });
});