/**
 * clock utility tests.
 */

import { createSystemClock, monotonicNowNs, memoryUsageBytes } from '../../src/util/clock';

describe('createSystemClock', () => {
  it('returns a Clock where now() and wallNow() are positive numbers', () => {
    const clock = createSystemClock();
    expect(clock.now()).toBeGreaterThan(0);
    expect(clock.wallNow()).toBeGreaterThan(0);
  });

  it('returns numeric (not bigint) values', () => {
    const clock = createSystemClock();
    expect(typeof clock.now()).toBe('number');
    expect(typeof clock.wallNow()).toBe('number');
  });

  it('now and wallNow are non-decreasing across calls', () => {
    const clock = createSystemClock();
    const a = clock.now();
    const w = clock.wallNow();
    const b = clock.now();
    expect(b).toBeGreaterThanOrEqual(a);
    expect(w).toBeGreaterThan(0);
  });
});

describe('monotonicNowNs', () => {
  it('returns a positive bigint', () => {
    const t = monotonicNowNs();
    expect(typeof t).toBe('bigint');
    expect(t).toBeGreaterThan(0n);
  });

  it('returns strictly non-decreasing values', () => {
    const a = monotonicNowNs();
    const b = monotonicNowNs();
    expect(b).toBeGreaterThanOrEqual(a);
  });
});

describe('memoryUsageBytes', () => {
  it('returns a non-negative number', () => {
    const m = memoryUsageBytes();
    expect(typeof m).toBe('number');
    expect(m).toBeGreaterThanOrEqual(0);
  });
});
