/**
 * priority.ts — Priority + Severity enums + rank records.
 */

import {
  PRIORITIES,
  PRIORITY_RANK,
  isPriority,
  SEVERITIES,
  SEVERITY_RANK,
  isSeverity,
} from '../../src/enums/priority';

describe('enums/priority', () => {
  describe('PRIORITIES', () => {
    it('contains 6 priorities in ascending order', () => {
      expect(PRIORITIES).toEqual([
        'lowest',
        'low',
        'normal',
        'high',
        'highest',
        'critical',
      ]);
    });
    it('PRIORITY_RANK assigns unique ascending ranks', () => {
      expect(PRIORITY_RANK.lowest).toBe(0);
      expect(PRIORITY_RANK.low).toBe(1);
      expect(PRIORITY_RANK.normal).toBe(2);
      expect(PRIORITY_RANK.high).toBe(3);
      expect(PRIORITY_RANK.highest).toBe(4);
      expect(PRIORITY_RANK.critical).toBe(5);
    });
    it('isPriority accepts valid', () => {
      for (const p of PRIORITIES) {
        expect(isPriority(p)).toBe(true);
      }
    });
    it('isPriority rejects invalid', () => {
      expect(isPriority('urgent')).toBe(false);
      expect(isPriority(null)).toBe(false);
    });
    it('PRIORITY_RANK is frozen', () => {
      expect(Object.isFrozen(PRIORITY_RANK)).toBe(true);
    });
  });

  describe('SEVERITIES', () => {
    it('contains 4 severities', () => {
      expect(SEVERITIES).toEqual(['info', 'warn', 'error', 'fatal']);
    });
    it('SEVERITY_RANK assigns ascending ranks', () => {
      expect(SEVERITY_RANK.info).toBe(0);
      expect(SEVERITY_RANK.warn).toBe(1);
      expect(SEVERITY_RANK.error).toBe(2);
      expect(SEVERITY_RANK.fatal).toBe(3);
    });
    it('isSeverity accepts valid', () => {
      for (const s of SEVERITIES) {
        expect(isSeverity(s)).toBe(true);
      }
    });
    it('isSeverity rejects invalid', () => {
      expect(isSeverity('debug')).toBe(false);
      expect(isSeverity(undefined)).toBe(false);
    });
    it('SEVERITY_RANK is frozen', () => {
      expect(Object.isFrozen(SEVERITY_RANK)).toBe(true);
    });
  });
});
