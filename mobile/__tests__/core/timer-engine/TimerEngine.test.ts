/**
 * TimerEngine — core state machine and tick scheduler tests.
 *
 * Coverage:
 *   - construction validation
 *   - start / pause / resume / stop / reset transitions
 *   - invalid transitions throw AppError
 *   - tick emission at correct interval
 *   - totalElapsedMs accuracy
 *   - mode changes update tick interval
 *   - time scaling affects elapsed time
 *   - background / foreground lifecycle
 *   - multiple listeners receive all events
 *   - re-entrant: pause from inside tick handler
 */

import { AppError, TimerEngine, type TimerEvent } from '@core/timer-engine';

import { createTimerTestRig, FakeClockProvider, FakeMonotonicClock, FakeWallClock } from './fakes';

describe('TimerEngine — construction & state', () => {
  it('requires monotonic, wall, and clockProvider', () => {
    expect(
      () =>
        new TimerEngine({
          monotonic: undefined as unknown as FakeMonotonicClock,
          wall: new FakeWallClock(new FakeMonotonicClock()),
          clockProvider: new FakeClockProvider({ monotonic: new FakeMonotonicClock() }),
        }),
    ).toThrow(AppError);
  });

  it('starts in idle state with zero totals', () => {
    const rig = createTimerTestRig();
    expect(rig.engine.getState()).toBe('idle');
    expect(rig.engine.getTotalElapsedMs()).toBe(0);
    expect(rig.engine.getTickIndex()).toBe(0);
  });

  it('uses default mode and time scale', () => {
    const rig = createTimerTestRig();
    expect(rig.engine.getMode()).toBe('balanced');
    expect(rig.engine.getTimeScale()).toBe(1);
  });
});

describe('TimerEngine — lifecycle transitions', () => {
  it('start() transitions idle → running and emits started event', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    expect(rig.engine.getState()).toBe('running');
    const started = rig.events.find((e) => e.type === 'started');
    expect(started).toBeDefined();
  });

  it('start() is a no-op when already running', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    const startedCountBefore = rig.events.filter((e) => e.type === 'started').length;
    rig.engine.start();
    const startedCountAfter = rig.events.filter((e) => e.type === 'started').length;
    expect(startedCountAfter).toBe(startedCountBefore);
  });

  it('start() throws from paused (must use resume)', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.engine.pause();
    expect(() => rig.engine.start()).toThrow(AppError);
  });

  it('start() throws from stopped (must use reset first)', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.engine.stop();
    expect(() => rig.engine.start()).toThrow(AppError);
  });

  it('pause() transitions running → paused and emits paused event', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(150);
    rig.engine.pause();
    expect(rig.engine.getState()).toBe('paused');
    const paused = rig.events.find((e) => e.type === 'paused');
    expect(paused).toBeDefined();
  });

  it('pause() is a no-op when not running', () => {
    const rig = createTimerTestRig();
    rig.engine.pause();
    expect(rig.engine.getState()).toBe('idle');
    expect(rig.events.find((e) => e.type === 'paused')).toBeUndefined();
  });

  it('resume() transitions paused → running and emits resumed event', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(150);
    rig.engine.pause();
    rig.clock.advance(500);
    rig.engine.resume();
    expect(rig.engine.getState()).toBe('running');
    const resumed = rig.events.find((e) => e.type === 'resumed');
    expect(resumed).toBeDefined();
    if (resumed?.type === 'resumed') {
      expect(resumed.pausedForMs).toBeGreaterThanOrEqual(500);
    }
  });

  it('resume() is a no-op when not paused', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.engine.resume();
    expect(rig.engine.getState()).toBe('running');
    expect(rig.events.find((e) => e.type === 'resumed')).toBeUndefined();
  });

  it('stop() transitions running → stopped and emits stopped event', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(200);
    rig.engine.stop();
    expect(rig.engine.getState()).toBe('stopped');
    const stopped = rig.events.find((e) => e.type === 'stopped');
    expect(stopped).toBeDefined();
  });

  it('stop() transitions paused → stopped', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(100);
    rig.engine.pause();
    rig.engine.stop();
    expect(rig.engine.getState()).toBe('stopped');
  });

  it('stop() is a no-op when idle or stopped', () => {
    const rig = createTimerTestRig();
    rig.engine.stop();
    expect(rig.events.find((e) => e.type === 'stopped')).toBeUndefined();
    rig.engine.start();
    rig.engine.stop();
    rig.engine.stop();
    expect(rig.events.filter((e) => e.type === 'stopped')).toHaveLength(1);
  });

  it('reset() returns to idle and zeros all state', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(500);
    rig.engine.stop();
    rig.engine.reset();
    expect(rig.engine.getState()).toBe('idle');
    expect(rig.engine.getTotalElapsedMs()).toBe(0);
    expect(rig.engine.getTickIndex()).toBe(0);
    expect(rig.engine.getSessionStartedAtWallIso()).toBeNull();
  });

  it('reset() from running zeroes state without stopping first', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(200);
    rig.engine.reset();
    expect(rig.engine.getState()).toBe('idle');
    expect(rig.engine.getTotalElapsedMs()).toBe(0);
  });

  it('reset() from paused zeroes state', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.engine.pause();
    rig.engine.reset();
    expect(rig.engine.getState()).toBe('idle');
  });
});

describe('TimerEngine — tick emission', () => {
  it('emits ticks at the configured interval in balanced mode', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(1000);
    const ticks = rig.events.filter((e) => e.type === 'tick');
    // 1000ms / 100ms = 10 ticks (allow ±1 due to scheduling).
    expect(ticks.length).toBeGreaterThanOrEqual(9);
    expect(ticks.length).toBeLessThanOrEqual(10);
  });

  it('emits 60 ticks in 1 second at high-precision (16.67ms)', () => {
    const rig = createTimerTestRig('high-precision');
    rig.engine.start();
    rig.clock.advance(1000);
    const ticks = rig.events.filter((e) => e.type === 'tick');
    expect(ticks.length).toBeGreaterThanOrEqual(58);
    expect(ticks.length).toBeLessThanOrEqual(61);
  });

  it('emits 1 tick in 1 second at low-power (1000ms)', () => {
    const rig = createTimerTestRig('low-power');
    rig.engine.start();
    rig.clock.advance(1500);
    const ticks = rig.events.filter((e) => e.type === 'tick');
    expect(ticks.length).toBe(1);
  });

  it('does not emit ticks when paused', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(300);
    const ticksBeforePause = rig.events.filter((e) => e.type === 'tick').length;
    rig.engine.pause();
    const ticksAfterPauseStart = rig.events.filter((e) => e.type === 'tick').length;
    rig.clock.advance(1000);
    const ticksAfterPauseEnd = rig.events.filter((e) => e.type === 'tick').length;
    expect(ticksBeforePause).toBeGreaterThan(0);
    expect(ticksAfterPauseStart).toBe(ticksBeforePause);
    expect(ticksAfterPauseEnd).toBe(ticksAfterPauseStart);
  });

  it('resumes tick emission after resume()', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(200);
    rig.engine.pause();
    const ticksAfterPause = rig.events.filter((e) => e.type === 'tick').length;
    rig.clock.advance(500);
    rig.engine.resume();
    rig.clock.advance(300);
    const ticksAfterResume = rig.events.filter((e) => e.type === 'tick').length;
    expect(ticksAfterResume).toBeGreaterThan(ticksAfterPause);
  });
});

describe('TimerEngine — elapsed time', () => {
  it('accumulates elapsed time during running', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(500);
    const elapsed = rig.engine.getTotalElapsedMs();
    expect(elapsed).toBeGreaterThanOrEqual(495);
    expect(elapsed).toBeLessThanOrEqual(510);
  });

  it('does not accumulate time while paused', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(200);
    rig.engine.pause();
    const elapsedAtPause = rig.engine.getTotalElapsedMs();
    rig.clock.advance(2000);
    const elapsedAfterWait = rig.engine.getTotalElapsedMs();
    expect(elapsedAfterWait).toBe(elapsedAtPause);
  });

  it('tracks total paused time', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(100);
    rig.engine.pause();
    rig.clock.advance(500);
    rig.engine.resume();
    expect(rig.engine.getTotalPausedMs()).toBeGreaterThanOrEqual(495);
    expect(rig.engine.getTotalPausedMs()).toBeLessThanOrEqual(510);
  });

  it('reset() zeros total paused time', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.engine.pause();
    rig.clock.advance(200);
    rig.engine.reset();
    expect(rig.engine.getTotalPausedMs()).toBe(0);
  });
});

describe('TimerEngine — mode and time scale', () => {
  it('setMode changes tick interval', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.engine.setMode('high-precision');
    expect(rig.engine.getMode()).toBe('high-precision');
    expect(rig.engine.getTickIntervalMs()).toBeCloseTo(16.667, 2);
  });

  it('setMode emits mode-changed event', () => {
    const rig = createTimerTestRig();
    rig.engine.setMode('low-power');
    const event = rig.events.find((e) => e.type === 'mode-changed');
    expect(event).toBeDefined();
    if (event?.type === 'mode-changed') {
      expect(event.currentMode).toBe('low-power');
      expect(event.tickIntervalMs).toBe(1000);
    }
  });

  it('setMode to same mode is a no-op (no event)', () => {
    const rig = createTimerTestRig();
    rig.engine.setMode('balanced');
    expect(rig.events.find((e) => e.type === 'mode-changed')).toBeUndefined();
  });

  it('setTimeScale accepts values in valid range', () => {
    const rig = createTimerTestRig();
    rig.engine.setTimeScale(2);
    expect(rig.engine.getTimeScale()).toBe(2);
  });

  it('setTimeScale rejects out-of-range values', () => {
    const rig = createTimerTestRig();
    expect(() => rig.engine.setTimeScale(0)).toThrow(AppError);
    expect(() => rig.engine.setTimeScale(-1)).toThrow(AppError);
    expect(() => rig.engine.setTimeScale(1001)).toThrow(AppError);
    expect(() => rig.engine.setTimeScale(Number.NaN)).toThrow(AppError);
  });

  it('time scale accelerates elapsed time', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.setTimeScale(2);
    rig.engine.start();
    rig.clock.advance(250);
    // 250 real ms * scale 2 = 500 engine ms.
    expect(rig.engine.getTotalElapsedMs()).toBeGreaterThanOrEqual(495);
    expect(rig.engine.getTotalElapsedMs()).toBeLessThanOrEqual(510);
  });

  it('setTimeScale emits time-scale-changed event', () => {
    const rig = createTimerTestRig();
    rig.engine.setTimeScale(2);
    const event = rig.events.find((e) => e.type === 'time-scale-changed');
    expect(event).toBeDefined();
  });
});

describe('TimerEngine — background/foreground', () => {
  it('notifyBackground pauses and emits backgrounded event', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.engine.notifyBackground();
    expect(rig.engine.getState()).toBe('paused');
    const event = rig.events.find((e) => e.type === 'backgrounded');
    expect(event).toBeDefined();
  });

  it('notifyForeground resumes and emits foregrounded event with duration', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(100);
    rig.engine.notifyBackground();
    rig.clock.advance(2000);
    rig.engine.notifyForeground();
    const event = rig.events.find((e) => e.type === 'foregrounded');
    expect(event).toBeDefined();
    if (event?.type === 'foregrounded') {
      expect(event.backgroundedForMs).toBeGreaterThanOrEqual(1990);
    }
  });

  it('notifyBackground is a no-op when not running', () => {
    const rig = createTimerTestRig();
    rig.engine.notifyBackground();
    expect(rig.events.find((e) => e.type === 'backgrounded')).toBeUndefined();
  });

  it('notifyForeground is a no-op when not backgrounded', () => {
    const rig = createTimerTestRig();
    rig.engine.notifyForeground();
    expect(rig.events.find((e) => e.type === 'foregrounded')).toBeUndefined();
  });

  it('does not accumulate elapsed time during background', () => {
    const rig = createTimerTestRig();
    rig.engine.start();
    rig.clock.advance(200);
    const elapsedBeforeBg = rig.engine.getTotalElapsedMs();
    rig.engine.notifyBackground();
    rig.clock.advance(5000);
    rig.engine.notifyForeground();
    const elapsedAfterBg = rig.engine.getTotalElapsedMs();
    expect(elapsedAfterBg).toBe(elapsedBeforeBg);
  });
});

describe('TimerEngine — multiple listeners and reentrancy', () => {
  it('dispatches to all subscribers', () => {
    const rig = createTimerTestRig('balanced');
    const received: TimerEvent[] = [];
    const off1 = rig.engine.subscribe((e) => {
      received.push(e);
    });
    const off2 = rig.engine.subscribe((e) => {
      received.push(e);
    });
    rig.engine.start();
    expect(received).toHaveLength(2);
    off1();
    off2();
  });

  it('pause() from inside a tick handler works (re-entrancy)', () => {
    const rig = createTimerTestRig('balanced');
    let didPause = false;
    rig.engine.subscribe((e) => {
      if (e.type === 'tick' && !didPause) {
        didPause = true;
        rig.engine.pause();
      }
    });
    rig.engine.start();
    rig.clock.advance(150);
    expect(rig.engine.getState()).toBe('paused');
  });

  it('listener errors do not break other listeners or the engine', () => {
    const rig = createTimerTestRig();
    const errors: unknown[] = [];
    const off = rig.engine.subscribe(() => {
      throw new Error('boom');
    });
    const received: TimerEvent[] = [];
    const off2 = rig.engine.subscribe((e) => {
      received.push(e);
    });
    rig.engine.start();
    expect(received).toHaveLength(1);
    off();
    off2();
    void errors;
  });
});

describe('TimerEngine — snapshot and accessors', () => {
  it('snapshot() reflects current state', () => {
    const rig = createTimerTestRig('low-power');
    rig.engine.start();
    rig.clock.advance(100);
    const snap = rig.engine.snapshot();
    expect(snap.state).toBe('running');
    expect(snap.mode).toBe('low-power');
    expect(snap.tickIntervalMs).toBe(1000);
    expect(snap.tickIndex).toBe(0);
    expect(snap.listenerCount).toBe(1);
  });
});
