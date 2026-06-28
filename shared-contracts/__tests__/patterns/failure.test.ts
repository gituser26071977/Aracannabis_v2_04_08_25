/**
 * failure.ts — Failure, isFailure, groupFailuresBySeverity, hasBlockingFailures.
 */

import {
  Failure,
  isFailure,
  groupFailuresBySeverity,
  hasBlockingFailures,
} from '../../src/patterns/failure';

describe('patterns/failure', () => {
  describe('Failure constructor', () => {
    it('builds frozen failure with required fields', () => {
      const f = Failure({ code: 'x', message: 'y', severity: 'error' });
      expect(f.code).toBe('x');
      expect(f.message).toBe('y');
      expect(f.severity).toBe('error');
      expect(f.path).toBeUndefined();
      expect(f.context).toBeUndefined();
      expect(Object.isFrozen(f)).toBe(true);
    });
    it('includes path when provided', () => {
      const f = Failure({ code: 'x', message: 'y', severity: 'warn', path: 'a.b' });
      expect(f.path).toBe('a.b');
    });
    it('includes context when provided', () => {
      const ctx = { line: 1 };
      const f = Failure({ code: 'x', message: 'y', severity: 'info', context: ctx });
      expect(f.context).toBe(ctx);
    });
  });

  describe('isFailure', () => {
    it('accepts well-formed failures', () => {
      expect(isFailure({ code: 'c', message: 'm', severity: 'error' })).toBe(true);
    });
    it('rejects missing code', () => {
      expect(isFailure({ message: 'm', severity: 'error' })).toBe(false);
    });
    it('rejects missing message', () => {
      expect(isFailure({ code: 'c', severity: 'error' })).toBe(false);
    });
    it('rejects missing severity', () => {
      expect(isFailure({ code: 'c', message: 'm' })).toBe(false);
    });
    it('rejects null', () => {
      expect(isFailure(null)).toBe(false);
    });
    it('rejects non-object', () => {
      expect(isFailure('string')).toBe(false);
      expect(isFailure(42)).toBe(false);
      expect(isFailure(undefined)).toBe(false);
    });
  });

  describe('groupFailuresBySeverity', () => {
    it('groups by severity', () => {
      const f1 = Failure({ code: 'a', message: 'm', severity: 'error' });
      const f2 = Failure({ code: 'b', message: 'm', severity: 'warn' });
      const f3 = Failure({ code: 'c', message: 'm', severity: 'fatal' });
      const grouped = groupFailuresBySeverity([f1, f2, f3]);
      expect(grouped.error).toEqual([f1]);
      expect(grouped.warn).toEqual([f2]);
      expect(grouped.fatal).toEqual([f3]);
      expect(grouped.info).toEqual([]);
    });
    it('returns all empty for empty list', () => {
      const grouped = groupFailuresBySeverity([]);
      expect(grouped.info).toEqual([]);
      expect(grouped.warn).toEqual([]);
      expect(grouped.error).toEqual([]);
      expect(grouped.fatal).toEqual([]);
    });
    it('returns frozen record', () => {
      const grouped = groupFailuresBySeverity([]);
      expect(Object.isFrozen(grouped)).toBe(true);
      expect(Object.isFrozen(grouped.info)).toBe(true);
    });
  });

  describe('hasBlockingFailures', () => {
    it('returns true when any error', () => {
      const f = Failure({ code: 'c', message: 'm', severity: 'error' });
      expect(hasBlockingFailures([f])).toBe(true);
    });
    it('returns true when any fatal', () => {
      const f = Failure({ code: 'c', message: 'm', severity: 'fatal' });
      expect(hasBlockingFailures([f])).toBe(true);
    });
    it('returns false when only warn', () => {
      const f = Failure({ code: 'c', message: 'm', severity: 'warn' });
      expect(hasBlockingFailures([f])).toBe(false);
    });
    it('returns false when only info', () => {
      const f = Failure({ code: 'c', message: 'm', severity: 'info' });
      expect(hasBlockingFailures([f])).toBe(false);
    });
    it('returns false for empty list', () => {
      expect(hasBlockingFailures([])).toBe(false);
    });
  });
});
