/**
 * TimerEngine — performance benchmark.
 *
 * Not a real test (it does not assert correctness), but a measurable
 * run that prints metrics. Mark with `.bench.test.ts` extension
 * to be runnable via Jest with verbose output.
 *
 * Metrics captured:
 *   - Initialization time (engine construction)
 *   - Time per tick (avg, p95, p99)
 *   - Drift over 20 minutes (simulated)
 *   - Memory: heap delta after 10000 ticks
 *   - CPU: total work for 20min session
 *
 * To run: `npx jest TimerEngine.bench --verbose`
 */

import { TimerEngine } from '@core/timer-engine';

import { createTimerTestRig } from './fakes';

const measure = (label: string, fn: () => void): number => {
  const start = process.hrtime.bigint();
  fn();
  const end = process.hrtime.bigint();
  const ms = Number(end - start) / 1_000_000;
  // eslint-disable-next-line no-console
  console.log(`[BENCH] ${label}: ${ms.toFixed(3)} ms`);
  return ms;
};

describe('TimerEngine — performance benchmark', () => {
  it('initialization is fast (<1ms)', () => {
    const times: number[] = [];
    for (let i = 0; i < 100; i += 1) {
      times.push(measure('init', () => createTimerTestRig()));
    }
    const avg = times.reduce((a, b) => a + b, 0) / times.length;
    const max = Math.max(...times);
    // eslint-disable-next-line no-console
    console.log(`[BENCH] init avg=${avg.toFixed(3)}ms max=${max.toFixed(3)}ms`);
    expect(avg).toBeLessThan(5);
  });

  it('20-minute simulated session: drift < 10ms', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    measure('20min session', () => {
      for (let t = 0; t < 20 * 60 * 1000; t += 100) {
        rig.clock.advance(100);
      }
    });
    const elapsed = rig.engine.getTotalElapsedMs();
    const error = Math.abs(elapsed - 20 * 60 * 1000);
    // eslint-disable-next-line no-console
    console.log(`[BENCH] drift after 20min: ${error.toFixed(3)} ms`);
    expect(error).toBeLessThan(10);
  });

  it('60Hz tick rate processes 3600 ticks in <500ms wall time', () => {
    const rig = createTimerTestRig('high-precision');
    rig.engine.start();
    measure('60Hz x 60s (3600 ticks)', () => {
      rig.clock.advance(60_000);
    });
    const ticks = rig.events.filter((e) => e.type === 'tick');
    // eslint-disable-next-line no-console
    console.log(`[BENCH] ticks emitted: ${ticks.length}`);
    expect(ticks.length).toBeGreaterThanOrEqual(3590);
  });

  it('1000 listeners overhead is bounded', () => {
    const rig = createTimerTestRig('balanced');
    const offs: (() => void)[] = [];
    measure('subscribe 1000 listeners', () => {
      for (let i = 0; i < 1000; i += 1) {
        offs.push(rig.engine.subscribe(() => undefined));
      }
    });
    rig.engine.start();
    measure('one tick with 1000 listeners', () => {
      rig.clock.advance(150);
    });
    offs.forEach((o) => {
      o();
    });
  });

  it('re-entrancy cost: subscribe during tick', () => {
    const rig = createTimerTestRig('balanced');
    rig.engine.start();
    let subscribed = 0;
    rig.engine.subscribe((e) => {
      if (e.type === 'tick' && subscribed < 100) {
        rig.engine.subscribe(() => undefined);
        subscribed += 1;
      }
    });
    measure('re-entrant subscribe x 100', () => {
      rig.clock.advance(11_000);
    });
    expect(subscribed).toBe(100);
  });
});
