/**
 * Test fakes for the Breath Engine.
 *
 * Builds on top of Timer Engine fakes. Provides a helper that wires
 * Timer Engine + Breath Engine together with fakes for deterministic
 * testing.
 *
 * Conventions:
 *   - `createBreathTestRig(config)` returns everything a test needs:
 *     monotonic clock, fake clock provider, timer engine, breath engine,
 *     and a recorder for emitted breath events.
 *   - Tests advance virtual time via `rig.clock.advance(ms)` which
 *     fires Timer Engine ticks, which in turn drive Breath Engine.
 */

import {
  TimerEngine,
  type MonotonicClock,
  type TimerEvent,
} from '@core/timer-engine';

import {
  BreathEngine,
  type BreathCycleConfig,
  type BreathEvent,
} from '@core/breath-engine';

import {
  FakeClockProvider,
  FakeMonotonicClock,
  FakeWallClock,
} from '../timer-engine/fakes';

export interface BreathTestRig {
  readonly monotonic: FakeMonotonicClock;
  readonly wall: FakeWallClock;
  readonly clock: FakeClockProvider;
  readonly timerEngine: TimerEngine;
  readonly breathEngine: BreathEngine;
  readonly breathEvents: BreathEvent[];
  readonly timerEvents: TimerEvent[];
  unsubscribe: () => void;
  reset(): void;
}

export const createBreathTestRig = (
  config: BreathCycleConfig,
  options: { timerMode?: 'high-precision' | 'balanced' | 'low-power' } = {},
): BreathTestRig => {
  const monotonic = new FakeMonotonicClock();
  const wall = new FakeWallClock(monotonic);
  const clock = new FakeClockProvider({ monotonic });
  const timerEngine = new TimerEngine({
    monotonic,
    wall,
    clockProvider: clock,
    mode: options.timerMode ?? 'balanced',
  });

  const breathEngine = new BreathEngine({
    monotonic: monotonic as MonotonicClock,
    timerEngine,
    config,
  });

  const breathEvents: BreathEvent[] = [];
  const timerEvents: TimerEvent[] = [];

  const offBreath = breathEngine.subscribe((e) => breathEvents.push(e));
  const offTimer = timerEngine.subscribe((e) => timerEvents.push(e));

  // Start the timer so Breath Engine can operate.
  timerEngine.start();

  return {
    monotonic,
    wall,
    clock,
    timerEngine,
    breathEngine,
    breathEvents,
    timerEvents,
    unsubscribe: (): void => {
      offBreath();
      offTimer();
    },
    reset: (): void => {
      breathEvents.length = 0;
      timerEvents.length = 0;
    },
  };
};