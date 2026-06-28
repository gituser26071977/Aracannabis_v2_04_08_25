/**
 * numeric.ts — Duration, Timestamp, Percentage, Progress, indices.
 *
 * Coverage:
 *   - Duration: constructor, DurationFromSeconds, DurationFromMinutes, DurationZero, conversions
 *   - Timestamp: constructor, TimestampNow, timestampDifference
 *   - Percentage: 0..100 validation
 *   - Progress: 0..1 validation, ProgressFromPercentage
 *   - CycleIndex, PhaseIndex: non-negative integer validation
 *   - Iso8601: format validation, Iso8601FromTimestamp, Iso8601ToTimestamp
 */

import {
  Duration,
  DurationFromSeconds,
  DurationFromMinutes,
  DurationZero,
  durationToSeconds,
  durationToMinutes,
  MAX_DURATION_MS,
  Timestamp,
  TimestampNow,
  timestampDifference,
  MAX_TIMESTAMP_MS,
  Percentage,
  Progress,
  ProgressFromPercentage,
  CycleIndex,
  PhaseIndex,
  Iso8601,
  Iso8601FromTimestamp,
  Iso8601ToTimestamp,
} from '../../src/value-objects/numeric';

describe('value-objects/numeric', () => {
  describe('Duration', () => {
    it('accepts zero', () => {
      expect(Duration(0)).toBe(0);
    });
    it('accepts positive integers within range', () => {
      expect(Duration(1000)).toBe(1000);
      expect(Duration(MAX_DURATION_MS)).toBe(MAX_DURATION_MS);
    });
    it('rejects negative', () => {
      expect(() => Duration(-1)).toThrow(/Invalid Duration/);
    });
    it('rejects non-integer', () => {
      expect(() => Duration(1.5)).toThrow(/Invalid Duration/);
    });
    it('rejects over MAX_DURATION_MS', () => {
      expect(() => Duration(MAX_DURATION_MS + 1)).toThrow(/Invalid Duration/);
    });
    it('rejects NaN/Infinity', () => {
      expect(() => Duration(NaN)).toThrow(/Invalid Duration/);
      expect(() => Duration(Infinity)).toThrow(/Invalid Duration/);
    });
    it('error code is invalid_duration', () => {
      try {
        Duration(-1);
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_duration');
      }
    });

    it('DurationFromSeconds rounds to ms', () => {
      expect(DurationFromSeconds(1)).toBe(1000);
      expect(DurationFromSeconds(0.5)).toBe(500);
      expect(DurationFromSeconds(0.001)).toBe(1);
    });
    it('DurationFromSeconds rejects out-of-range', () => {
      expect(() => DurationFromSeconds(-1)).toThrow();
    });

    it('DurationFromMinutes rounds to ms', () => {
      expect(DurationFromMinutes(1)).toBe(60_000);
      expect(DurationFromMinutes(2.5)).toBe(150_000);
    });

    it('DurationZero returns 0', () => {
      expect(DurationZero()).toBe(0);
    });

    it('durationToSeconds and durationToMinutes', () => {
      const d = Duration(60_000);
      expect(durationToSeconds(d)).toBe(60);
      expect(durationToMinutes(d)).toBe(1);
    });
  });

  describe('Timestamp', () => {
    it('accepts zero', () => {
      expect(Timestamp(0)).toBe(0);
    });
    it('accepts current epoch ms', () => {
      const t = Timestamp(Date.now());
      expect(typeof t).toBe('number');
    });
    it('accepts max', () => {
      expect(Timestamp(MAX_TIMESTAMP_MS)).toBe(MAX_TIMESTAMP_MS);
    });
    it('rejects negative', () => {
      expect(() => Timestamp(-1)).toThrow(/Invalid Timestamp/);
    });
    it('rejects non-integer', () => {
      expect(() => Timestamp(1.5)).toThrow(/Invalid Timestamp/);
    });
    it('rejects over MAX', () => {
      expect(() => Timestamp(MAX_TIMESTAMP_MS + 1)).toThrow(/Invalid Timestamp/);
    });
    it('TimestampNow uses provided clock', () => {
      const t = TimestampNow(() => 12345);
      expect(t).toBe(12345);
    });
    it('TimestampNow defaults to Date.now', () => {
      const t = TimestampNow();
      expect(Math.abs((t as unknown as number) - Date.now())).toBeLessThan(100);
    });
    it('timestampDifference returns duration between timestamps', () => {
      const a = Timestamp(1000);
      const b = Timestamp(2500);
      expect(timestampDifference(b, a)).toBe(1500);
    });
  });

  describe('Percentage', () => {
    it('accepts boundary 0 and 100', () => {
      expect(Percentage(0)).toBe(0);
      expect(Percentage(100)).toBe(100);
    });
    it('accepts mid values', () => {
      expect(Percentage(50.5)).toBe(50.5);
    });
    it('rejects below 0', () => {
      expect(() => Percentage(-0.1)).toThrow(/Invalid Percentage/);
    });
    it('rejects above 100', () => {
      expect(() => Percentage(100.1)).toThrow(/Invalid Percentage/);
    });
    it('rejects NaN/Infinity', () => {
      expect(() => Percentage(NaN)).toThrow(/Invalid Percentage/);
      expect(() => Percentage(Infinity)).toThrow(/Invalid Percentage/);
    });
  });

  describe('Progress', () => {
    it('accepts boundary 0 and 1', () => {
      expect(Progress(0)).toBe(0);
      expect(Progress(1)).toBe(1);
    });
    it('accepts mid values', () => {
      expect(Progress(0.5)).toBe(0.5);
    });
    it('rejects below 0', () => {
      expect(() => Progress(-0.1)).toThrow(/Invalid Progress/);
    });
    it('rejects above 1', () => {
      expect(() => Progress(1.1)).toThrow(/Invalid Progress/);
    });
    it('ProgressFromPercentage divides by 100', () => {
      expect(ProgressFromPercentage(Percentage(0))).toBe(0);
      expect(ProgressFromPercentage(Percentage(50))).toBe(0.5);
      expect(ProgressFromPercentage(Percentage(100))).toBe(1);
    });
  });

  describe('CycleIndex', () => {
    it('accepts zero', () => {
      expect(CycleIndex(0)).toBe(0);
    });
    it('accepts positive integers', () => {
      expect(CycleIndex(42)).toBe(42);
    });
    it('rejects negative', () => {
      expect(() => CycleIndex(-1)).toThrow(/Invalid CycleIndex/);
    });
    it('rejects non-integer', () => {
      expect(() => CycleIndex(1.5)).toThrow(/Invalid CycleIndex/);
    });
  });

  describe('PhaseIndex', () => {
    it('accepts zero', () => {
      expect(PhaseIndex(0)).toBe(0);
    });
    it('accepts positive integers', () => {
      expect(PhaseIndex(7)).toBe(7);
    });
    it('rejects negative', () => {
      expect(() => PhaseIndex(-1)).toThrow(/Invalid PhaseIndex/);
    });
    it('rejects non-integer', () => {
      expect(() => PhaseIndex(0.5)).toThrow(/Invalid PhaseIndex/);
    });
  });

  describe('Iso8601', () => {
    it('accepts valid ISO 8601', () => {
      expect(Iso8601('2024-01-15T10:30:00Z')).toBe('2024-01-15T10:30:00Z');
      expect(Iso8601('2024-01-15T10:30:00.000Z')).toBe('2024-01-15T10:30:00.000Z');
    });
    it('rejects empty', () => {
      expect(() => Iso8601('')).toThrow(/Invalid Iso8601/);
    });
    it('rejects invalid format', () => {
      expect(() => Iso8601('not-a-date')).toThrow(/Invalid Iso8601/);
    });
    it('Iso8601FromTimestamp produces valid ISO string', () => {
      const ts = Timestamp(0);
      const iso = Iso8601FromTimestamp(ts);
      expect(typeof iso).toBe('string');
      expect(Iso8601ToTimestamp(iso)).toBe(0);
    });
    it('Iso8601ToTimestamp parses back', () => {
      const iso = Iso8601('2024-01-15T10:30:00.000Z');
      const ts = Iso8601ToTimestamp(iso);
      expect(typeof ts).toBe('number');
      expect(new Date(ts as number).toISOString()).toBe('2024-01-15T10:30:00.000Z');
    });
  });
});
