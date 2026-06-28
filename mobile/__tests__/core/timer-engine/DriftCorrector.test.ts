/**
 * DriftCorrector tests.
 *
 * Coverage:
 *   - computeNextDelayMs compensates positive drift
 *   - computeNextDelayMs compensates negative drift
 *   - computeNextDelayMs clamps to [1, 2*interval]
 *   - recordTick returns null for sub-millisecond drift
 *   - recordTick accumulates drift across calls
 */

import { createDriftCorrector, type DriftCorrectionStrategy } from '@core/timer-engine';
import { FakeMonotonicClock } from './fakes';

describe('DriftCorrector', () => {
  let drift: DriftCorrectionStrategy;
  beforeEach(() => {
    drift = createDriftCorrector(new FakeMonotonicClock());
  });

  describe('computeNextDelayMs', () => {
    it('returns interval when previous drift is zero', () => {
      const next = drift.computeNextDelayMs({
        intervalMs: 100,
        previousDriftMs: 0,
        previousNextDelayMs: 100,
        actualElapsedMs: 0,
      });
      expect(next).toBe(100);
    });

    it('reduces delay to compensate for late ticks', () => {
      const next = drift.computeNextDelayMs({
        intervalMs: 100,
        previousDriftMs: 5, // tick ran 5ms late
        previousNextDelayMs: 100,
        actualElapsedMs: 105,
      });
      expect(next).toBe(95);
    });

    it('increases delay to compensate for early ticks', () => {
      const next = drift.computeNextDelayMs({
        intervalMs: 100,
        previousDriftMs: -5,
        previousNextDelayMs: 100,
        actualElapsedMs: 95,
      });
      expect(next).toBe(105);
    });

    it('clamps to minimum of 1ms', () => {
      const next = drift.computeNextDelayMs({
        intervalMs: 100,
        previousDriftMs: 1000, // way overcompensated
        previousNextDelayMs: 100,
        actualElapsedMs: 1100,
      });
      expect(next).toBe(1);
    });

    it('clamps to maximum of 2*interval', () => {
      const next = drift.computeNextDelayMs({
        intervalMs: 100,
        previousDriftMs: -500, // way undercompensated
        previousNextDelayMs: 100,
        actualElapsedMs: -400,
      });
      expect(next).toBe(200);
    });
  });

  describe('recordTick', () => {
    it('returns null for sub-millisecond drift', () => {
      const m = drift.recordTick({ tickIndex: 0, intervalMs: 100, actualElapsedMs: 100 });
      expect(m).toBeNull();
    });

    it('returns measurement for positive drift >= 1ms', () => {
      const m = drift.recordTick({ tickIndex: 0, intervalMs: 100, actualElapsedMs: 105 });
      expect(m).not.toBeNull();
      expect(m?.driftMs).toBe(5);
      expect(m?.cumulativeDriftMs).toBe(5);
    });

    it('returns measurement for negative drift <= -1ms', () => {
      const m = drift.recordTick({ tickIndex: 0, intervalMs: 100, actualElapsedMs: 95 });
      expect(m).not.toBeNull();
      expect(m?.driftMs).toBe(-5);
      expect(m?.cumulativeDriftMs).toBe(-5);
    });

    it('accumulates drift across calls', () => {
      drift.recordTick({ tickIndex: 0, intervalMs: 100, actualElapsedMs: 103 });
      drift.recordTick({ tickIndex: 1, intervalMs: 100, actualElapsedMs: 205 });
      const m = drift.recordTick({ tickIndex: 2, intervalMs: 100, actualElapsedMs: 308 });
      expect(m).not.toBeNull();
      expect(m?.cumulativeDriftMs).toBe(308 - 300);
    });

    it('filters sub-millisecond noise but tracks cumulative state', () => {
      drift.recordTick({ tickIndex: 0, intervalMs: 100, actualElapsedMs: 100 });
      drift.recordTick({ tickIndex: 1, intervalMs: 100, actualElapsedMs: 200 });
      const m = drift.recordTick({ tickIndex: 2, intervalMs: 100, actualElapsedMs: 302 });
      expect(m).not.toBeNull();
      expect(m?.driftMs).toBe(2);
    });
  });
});
