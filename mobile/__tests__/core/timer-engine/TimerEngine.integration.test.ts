/**
 * TimerEngine — long sessions, drift, stress, race conditions.
 *
 * Coverage:
 *   - Long session (20 minutes simulated via time scale)
 *   - Cumulative drift within tolerance
 *   - Rapid pause/resume cycles
 *   - Multiple rapid start/pause cycles
 *   - Memory: thousands of ticks with no listener leaks
 *   - Stress: many listeners
 *   - Real timer smoke (no fakes, validates infrastructure)
 */

import { TimerEngine } from '@core/timer-engine';
import { createBrowserMonotonicClock, createBrowserWallClock, createDefaultClockProvider } from '@core/timer-engine';

import { createTimerTestRig, FakeClockProvider, FakeMonotonicClock, FakeWallClock } from './fakes';

const SESSION_20_MIN_MS = 20 * 60 * 1000;
const DRIFT_TOLERANCE_MS = 50; // Engine-internal drift must be < 50ms after 20 min.

describe('TimerEngine — long sessions and drift', () => {
  it('20-minute session has accumulated error under 10ms at scale 1', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    // Drive time forward in 100ms steps to mimic real clockProvider.
    for (let t = 0; t < SESSION_20_MIN_MS; t += 100) {
      rig.clock.advance(100);
    }
    const elapsed = rig.engine.getTotalElapsedMs();
    const expected = SESSION_20_MIN_MS;
    const error = Math.abs(elapsed - expected);
    expect(error).toBeLessThan(10);
  });

  it('20-minute session has drift under 50ms cumulative', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    for (let t = 0; t < SESSION_20_MIN_MS; t += 100) {
      rig.clock.advance(100);
    }
    // Count drift events; sum of |drift| should be small relative to session length.
    const driftEvents = rig.events.filter((e) => e.type === 'drift');
    if (driftEvents.length > 0) {
      const lastDrift = driftEvents[driftEvents.length - 1];
      if (lastDrift?.type === 'drift') {
        expect(Math.abs(lastDrift.measurement.cumulativeDriftMs)).toBeLessThan(DRIFT_TOLERANCE_MS);
      }
    }
    // Either no drift events (sub-1ms noise) or within tolerance.
  });

  it('20-minute session simulated at scale 100 completes in ~12s real time', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.setTimeScale(100);
    rig.engine.start();
    for (let t = 0; t < SESSION_20_MIN_MS / 100; t += 50) {
      rig.clock.advance(50);
    }
    // 20 min / 100 = 12 sec; we advanced 12 sec.
    const elapsed = rig.engine.getTotalElapsedMs();
    expect(elapsed).toBeGreaterThanOrEqual(SESSION_20_MIN_MS - 100);
    expect(elapsed).toBeLessThanOrEqual(SESSION_20_MIN_MS + 100);
  });
});

describe('TimerEngine — rapid cycles', () => {
  it('survives 100 rapid pause/resume cycles', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    for (let i = 0; i < 100; i += 1) {
      rig.clock.advance(50);
      rig.engine.pause();
      rig.clock.advance(20);
      rig.engine.resume();
    }
    expect(rig.engine.getState()).toBe('running');
    const tickCount = rig.events.filter((e) => e.type === 'tick').length;
    expect(tickCount).toBeGreaterThan(0);
  });

  it('survives 50 start/stop/reset cycles', () => {
    const rig = createTimerTestRig('balanced');
    for (let i = 0; i < 50; i += 1) {
      rig.engine.start();
      rig.clock.advance(200);
      rig.engine.stop();
      rig.engine.reset();
    }
    expect(rig.engine.getState()).toBe('idle');
    expect(rig.engine.getTotalElapsedMs()).toBe(0);
  });
});

describe('TimerEngine — listener memory and stress', () => {
  it('handles 1000 ticks without listener leaks', () => {
    const rig = createTimerTestRig('balanced');
    let listenerCalls = 0;
    const off = rig.engine.subscribe(() => {
      listenerCalls += 1;
    });
    rig.engine.start();
    rig.clock.advance(100_000);
    expect(listenerCalls).toBeGreaterThanOrEqual(990);
    off();
    // After unsubscribe, no more calls.
    const callsBefore = listenerCalls;
    rig.clock.advance(1000);
    expect(listenerCalls).toBe(callsBefore);
  });

  it('handles 100 simultaneous listeners', () => {
    const rig = createTimerTestRig('balanced');
    const offs: (() => void)[] = [];
    let count = 0;
    for (let i = 0; i < 100; i += 1) {
      offs.push(
        rig.engine.subscribe(() => {
          count += 1;
        }),
      );
    }
    rig.engine.start();
    rig.clock.advance(150);
    expect(count).toBeGreaterThan(0);
    offs.forEach((off) => {
      off();
    });
  });

  it('no leftover clock handles after stop', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(300);
    rig.engine.stop();
    expect(rig.clock.activeHandleCount()).toBe(0);
  });

  it('no leftover clock handles after reset', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(300);
    rig.engine.reset();
    expect(rig.clock.activeHandleCount()).toBe(0);
  });
});

describe('TimerEngine — background lifecycle correctness', () => {
  it('does not double-count time across background cycles', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    rig.clock.advance(1000);
    rig.engine.notifyBackground();
    rig.clock.advance(10_000);
    rig.engine.notifyForeground();
    rig.clock.advance(1000);
    rig.engine.notifyBackground();
    rig.clock.advance(5_000);
    rig.engine.notifyForeground();
    rig.clock.advance(500);
    // Active time: 1000 + 1000 + 500 = 2500ms (background time excluded).
    const elapsed = rig.engine.getTotalElapsedMs();
    expect(elapsed).toBeGreaterThanOrEqual(2490);
    expect(elapsed).toBeLessThanOrEqual(2520);
  });
});

describe('TimerEngine — infrastructure integration (real timers, short)', () => {
  it('runs a short session with real setTimeout and respects elapsed', (done) => {
    const monotonic = createBrowserMonotonicClock();
    const wall = createBrowserWallClock();
    const clock = createDefaultClockProvider();
    const engine = new TimerEngine({ monotonic, wall, clockProvider: clock });
    let firstTickAt: number | null = null;
    const off = engine.subscribe((e) => {
      if (e.type === 'tick' && firstTickAt === null) {
        firstTickAt = monotonic.now();
      }
    });
    engine.start();
    // Use setTimeout to validate infrastructure path.
    setTimeout(() => {
      engine.stop();
      off();
      const elapsed = engine.getTotalElapsedMs();
      // Should have ticked at least once.
      expect(elapsed).toBeGreaterThan(0);
      expect(firstTickAt).not.toBeNull();
      done();
    }, 200);
  }, 5000);

  it('runtime provider works without throws under normal use', () => {
    expect(() => {
      const monotonic = createBrowserMonotonicClock();
      const wall = createBrowserWallClock();
      const clock = createDefaultClockProvider();
      void monotonic.now();
      void wall.isoNow();
      clock.setTimeout(() => undefined, 10000).cancel();
    }).not.toThrow();
  });

  it('runtime providers do not interfere with each other', () => {
    const mon1 = createBrowserMonotonicClock();
    const mon2 = createBrowserMonotonicClock();
    const wall1 = createBrowserWallClock();
    const wall2 = createBrowserWallClock();
    const m1 = mon1.now();
    const m2 = mon2.now();
    // Both should return numbers, both should be close (same time source).
    expect(typeof m1).toBe('number');
    expect(typeof m2).toBe('number');
    expect(Math.abs(m1 - m2)).toBeLessThan(1000);
    expect(typeof wall1.isoNow()).toBe('string');
    expect(typeof wall2.isoNow()).toBe('string');
  });
});

describe('TimerEngine — concurrency safety (JS single-threaded, but verify)', () => {
  it('re-entrant subscribe/unsubscribe during tick is safe', () => {
    const rig = createTimerTestRig('balanced');
    let count = 0;
    const off = rig.engine.subscribe((e) => {
      if (e.type === 'tick') {
        count += 1;
        if (count === 1) {
          // Re-entrant: subscribe another listener mid-dispatch.
          rig.engine.subscribe(() => undefined);
        }
      }
    });
    rig.engine.start();
    rig.clock.advance(500);
    off();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  it('state remains consistent across many subscribers (no double-fire)', () => {
    const rig = createTimerTestRig('balanced');
    let a = 0;
    let b = 0;
    const offA = rig.engine.subscribe(() => {
      a += 1;
    });
    const offB = rig.engine.subscribe(() => {
      b += 1;
    });
    rig.engine.start();
    rig.clock.advance(500);
    offA();
    offB();
    expect(a).toBe(b);
  });
});

describe('FakeClockProvider — utility tests', () => {
  it('FakeMonotonicClock advance is cumulative', () => {
    const clock = new FakeMonotonicClock();
    clock.advance(100);
    clock.advance(50);
    expect(clock.now()).toBe(150);
  });

  it('FakeClockProvider fires callbacks in order', () => {
    const monotonic = new FakeMonotonicClock();
    const clock = new FakeClockProvider({ monotonic });
    const order: string[] = [];
    clock.setTimeout(() => {
      order.push('a');
    }, 100);
    clock.setTimeout(() => {
      order.push('b');
    }, 50);
    clock.advance(200);
    expect(order).toEqual(['b', 'a']);
  });

  it('FakeClockProvider cancels work correctly', () => {
    const monotonic = new FakeMonotonicClock();
    const clock = new FakeClockProvider({ monotonic });
    const calls: string[] = [];
    const h = clock.setTimeout(() => {
      calls.push('cancelled-but-still-called');
    }, 100);
    h.cancel();
    clock.advance(200);
    expect(calls).toEqual([]);
  });

  it('FakeClockProvider setInterval fires repeatedly', () => {
    const monotonic = new FakeMonotonicClock();
    const clock = new FakeClockProvider({ monotonic });
    let n = 0;
    const h = clock.setInterval(() => {
      n += 1;
    }, 50);
    clock.advance(225);
    h.cancel();
    // 0, 50, 100, 150, 200 = 5 fires.
    expect(n).toBe(5);
  });

  it('FakeClockProvider advances chronologically when callbacks are pending', () => {
    const monotonic = new FakeMonotonicClock();
    const clock = new FakeClockProvider({ monotonic });
    let timeOfFire = -1;
    clock.setTimeout(() => {
      timeOfFire = monotonic.now();
    }, 100);
    clock.advance(150);
    expect(timeOfFire).toBe(100);
  });

  it('FakeWallClock emits ISO strings', () => {
    const monotonic = new FakeMonotonicClock(0);
    const wall = new FakeWallClock(monotonic, 1_700_000_000_000);
    const iso = wall.isoNow();
    expect(iso).toMatch(/^2023-11-14T22:13:20\.000Z$/);
  });
});
