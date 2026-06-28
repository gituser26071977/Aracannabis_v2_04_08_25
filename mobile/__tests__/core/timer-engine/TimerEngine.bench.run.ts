/**
 * Real-time benchmark: runs a 30-second session using real setTimeout
 * to measure actual production behavior.
 *
 * Run with: npx ts-node mobile/__tests__/core/timer-engine/TimerEngine.bench.run.ts
 * Or: npx jest --testPathPattern TimerEngine.bench.run
 *
 * This is a smoke test, not a unit test. It validates that the
 * default infrastructure path works under real-time conditions.
 */

import { TimerEngine, createBrowserMonotonicClock, createBrowserWallClock, createDefaultClockProvider } from '@core/timer-engine';

const SESSION_DURATION_MS = 30_000;

describe('TimerEngine — real-time 30s benchmark', () => {
  it('runs 30s session with real setTimeout; reports drift', (done) => {
    const monotonic = createBrowserMonotonicClock();
    const wall = createBrowserWallClock();
    const clock = createDefaultClockProvider();
    const engine = new TimerEngine({ monotonic, wall, clockProvider: clock });
    const tickTimes: number[] = [];
    const off = engine.subscribe((e) => {
      if (e.type === 'tick') {
        tickTimes.push(e.monotonicMs);
      }
    });

    engine.start();
    const startWall = wall.now();
    const startMonotonic = monotonic.now();

    setTimeout(() => {
      engine.stop();
      off();

      const elapsedMonotonic = monotonic.now() - startMonotonic;
      const elapsedWall = wall.now() - startWall;

      // Compute jitter (variance between consecutive tick intervals).
      let jitters: number[] = [];
      for (let i = 1; i < tickTimes.length; i += 1) {
        const prev = tickTimes[i - 1];
        const cur = tickTimes[i];
        if (prev !== undefined && cur !== undefined) {
          jitters.push(cur - prev);
        }
      }
      const avgJitter =
        jitters.length > 0 ? jitters.reduce((a, b) => a + b, 0) / jitters.length : 0;
      const maxJitter = jitters.length > 0 ? Math.max(...jitters) : 0;
      const minJitter = jitters.length > 0 ? Math.min(...jitters) : 0;
      const drift = Math.abs(elapsedMonotonic - SESSION_DURATION_MS);
      const driftPct = (drift / SESSION_DURATION_MS) * 100;

      // eslint-disable-next-line no-console
      console.log(`
[BENCH — Real Time]
  Session:        ${SESSION_DURATION_MS}ms
  Wall elapsed:   ${elapsedWall}ms
  Mono elapsed:   ${elapsedMonotonic.toFixed(2)}ms
  Drift:          ${drift.toFixed(2)}ms (${driftPct.toFixed(4)}%)
  Ticks emitted:  ${tickTimes.length}
  Avg tick int:   ${avgJitter.toFixed(2)}ms
  Min tick int:   ${minJitter.toFixed(2)}ms
  Max tick int:   ${maxJitter.toFixed(2)}ms
  Engine elapsed: ${engine.getTotalElapsedMs().toFixed(2)}ms
`);

      // Sanity assertions.
      expect(tickTimes.length).toBeGreaterThan(290);
      expect(driftPct).toBeLessThan(1); // < 1% drift over 30s.

      done();
    }, SESSION_DURATION_MS);
  }, 35000);
});
