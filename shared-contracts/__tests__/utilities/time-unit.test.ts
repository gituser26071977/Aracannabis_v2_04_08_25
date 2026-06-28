/**
 * time-unit.ts — TimeUnit enum + conversions.
 */

import {
  TIME_UNITS,
  toMilliseconds,
  fromMilliseconds,
  isTimeUnit,
} from '../../src/utilities/time-unit';

describe('utilities/time-unit', () => {
  it('TIME_UNITS contains expected values', () => {
    expect(TIME_UNITS).toEqual(['millisecond', 'second', 'minute', 'hour', 'day']);
  });

  describe('toMilliseconds', () => {
    it('converts millisecond', () => {
      expect(toMilliseconds(5, 'millisecond')).toBe(5);
    });
    it('converts second', () => {
      expect(toMilliseconds(2, 'second')).toBe(2000);
    });
    it('converts minute', () => {
      expect(toMilliseconds(1, 'minute')).toBe(60_000);
    });
    it('converts hour', () => {
      expect(toMilliseconds(1, 'hour')).toBe(3_600_000);
    });
    it('converts day', () => {
      expect(toMilliseconds(1, 'day')).toBe(86_400_000);
    });
  });

  describe('fromMilliseconds', () => {
    it('converts to second', () => {
      expect(fromMilliseconds(2000, 'second')).toBe(2);
    });
    it('converts to minute', () => {
      expect(fromMilliseconds(120_000, 'minute')).toBe(2);
    });
    it('converts to hour', () => {
      expect(fromMilliseconds(7_200_000, 'hour')).toBe(2);
    });
    it('converts to day', () => {
      expect(fromMilliseconds(172_800_000, 'day')).toBe(2);
    });
    it('roundtrip ms→s→ms', () => {
      const ms = 5000;
      expect(toMilliseconds(fromMilliseconds(ms, 'second'), 'second')).toBe(ms);
    });
  });

  describe('isTimeUnit', () => {
    it('accepts valid units', () => {
      for (const u of TIME_UNITS) {
        expect(isTimeUnit(u)).toBe(true);
      }
    });
    it('rejects invalid', () => {
      expect(isTimeUnit('week')).toBe(false);
      expect(isTimeUnit(null)).toBe(false);
      expect(isTimeUnit(42)).toBe(false);
    });
  });
});
