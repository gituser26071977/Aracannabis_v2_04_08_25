/**
 * validation.ts — AppError + validation helpers.
 *
 * Coverage:
 *   - AppError: name, code, severity, context, cause, toJSON
 *   - isNonEmptyString, isFiniteNumber, isInteger, isInRange
 *   - Patterns: ULID, ISO8601, SEMVER, UUID v4
 */

import {
  AppError,
  ULID_PATTERN,
  ISO8601_PATTERN,
  SEMVER_PATTERN,
  UUID_V4_PATTERN,
  isNonEmptyString,
  isFiniteNumber,
  isInteger,
  isInRange,
} from '../../src/value-objects/validation';

describe('value-objects/validation', () => {
  describe('AppError', () => {
    it('exposes name, message, code, severity, context', () => {
      const err = new AppError('boom', {
        code: 'test_code',
        severity: 'error',
        context: { foo: 1 },
      });
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(AppError);
      expect(err.name).toBe('AppError');
      expect(err.message).toBe('boom');
      expect(err.code).toBe('test_code');
      expect(err.severity).toBe('error');
      expect(err.context).toEqual({ foo: 1 });
      expect(err.stack).toBeDefined();
    });

    it('defaults context to {} when omitted', () => {
      const err = new AppError('x', { code: 'c', severity: 'warn' });
      expect(err.context).toEqual({});
    });

    it('captures cause when provided', () => {
      const cause = new Error('inner');
      const err = new AppError('outer', { code: 'c', severity: 'fatal', cause });
      expect(err.cause).toBe(cause);
    });

    it('toJSON() returns serialized representation', () => {
      const cause = new Error('inner');
      const err = new AppError('msg', {
        code: 'c',
        severity: 'error',
        context: { a: 1 },
        cause,
      });
      const json = err.toJSON();
      expect(json).toMatchObject({
        name: 'AppError',
        message: 'msg',
        code: 'c',
        severity: 'error',
        context: { a: 1 },
        cause: 'inner',
      });
      expect(typeof json.stack).toBe('string');
    });

    it('toJSON() preserves non-Error cause as-is', () => {
      const err = new AppError('msg', {
        code: 'c',
        severity: 'error',
        cause: 'plain-string',
      });
      expect(err.toJSON().cause).toBe('plain-string');
    });

    it('preserves cause=undefined as undefined', () => {
      const err = new AppError('m', { code: 'c', severity: 'info' });
      expect(err.cause).toBeUndefined();
    });

    it('preserves all severity values', () => {
      const severities: Array<'info' | 'warn' | 'error' | 'fatal'> = [
        'info',
        'warn',
        'error',
        'fatal',
      ];
      for (const sev of severities) {
        const e = new AppError('m', { code: 'c', severity: sev });
        expect(e.severity).toBe(sev);
      }
    });
  });

  describe('isNonEmptyString', () => {
    it('returns true for non-empty strings', () => {
      expect(isNonEmptyString('x')).toBe(true);
      expect(isNonEmptyString(' ')).toBe(true);
    });
    it('returns false for empty string', () => {
      expect(isNonEmptyString('')).toBe(false);
    });
    it('returns false for non-strings', () => {
      expect(isNonEmptyString(null)).toBe(false);
      expect(isNonEmptyString(undefined)).toBe(false);
      expect(isNonEmptyString(1)).toBe(false);
      expect(isNonEmptyString({})).toBe(false);
    });
  });

  describe('isFiniteNumber', () => {
    it('returns true for finite numbers', () => {
      expect(isFiniteNumber(0)).toBe(true);
      expect(isFiniteNumber(-1)).toBe(true);
      expect(isFiniteNumber(1.5)).toBe(true);
    });
    it('returns false for Infinity, NaN', () => {
      expect(isFiniteNumber(Infinity)).toBe(false);
      expect(isFiniteNumber(-Infinity)).toBe(false);
      expect(isFiniteNumber(NaN)).toBe(false);
    });
    it('returns false for non-numbers', () => {
      expect(isFiniteNumber('1')).toBe(false);
      expect(isFiniteNumber(null)).toBe(false);
      expect(isFiniteNumber(undefined)).toBe(false);
    });
  });

  describe('isInteger', () => {
    it('returns true for integers', () => {
      expect(isInteger(0)).toBe(true);
      expect(isInteger(-1)).toBe(true);
      expect(isInteger(1)).toBe(true);
    });
    it('returns false for non-integers', () => {
      expect(isInteger(1.5)).toBe(false);
      expect(isInteger(NaN)).toBe(false);
      expect(isInteger('1')).toBe(false);
    });
  });

  describe('isInRange', () => {
    it('returns true for in-range inclusive', () => {
      expect(isInRange(0, 0, 10)).toBe(true);
      expect(isInRange(5, 0, 10)).toBe(true);
      expect(isInRange(10, 0, 10)).toBe(true);
    });
    it('returns false for out-of-range', () => {
      expect(isInRange(-1, 0, 10)).toBe(false);
      expect(isInRange(11, 0, 10)).toBe(false);
    });
  });

  describe('Patterns', () => {
    const validUlid = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
    const validIso = '2024-01-15T10:30:00.000Z';
    const validSemver = '1.2.3';
    const validUuidV4 = 'REDACTED';

    it('ULID_PATTERN accepts valid ULID', () => {
      expect(ULID_PATTERN.test(validUlid)).toBe(true);
    });
    it('ULID_PATTERN rejects invalid ULID', () => {
      expect(ULID_PATTERN.test('invalid')).toBe(false);
      expect(ULID_PATTERN.test('')).toBe(false);
      expect(ULID_PATTERN.test('01ARZ3NDEKTSV4RRFFQ69G5FA')).toBe(false); // 25 chars
    });

    it('ISO8601_PATTERN accepts valid ISO 8601', () => {
      expect(ISO8601_PATTERN.test(validIso)).toBe(true);
      expect(ISO8601_PATTERN.test('2024-01-15T10:30:00Z')).toBe(true);
      expect(ISO8601_PATTERN.test('2024-01-15T10:30:00+03:00')).toBe(true);
    });
    it('ISO8601_PATTERN rejects invalid ISO 8601', () => {
      expect(ISO8601_PATTERN.test('2024-01-15')).toBe(false);
      expect(ISO8601_PATTERN.test('not-a-date')).toBe(false);
      expect(ISO8601_PATTERN.test('')).toBe(false);
    });

    it('SEMVER_PATTERN accepts valid semver', () => {
      expect(SEMVER_PATTERN.test(validSemver)).toBe(true);
      expect(SEMVER_PATTERN.test('1.0.0-alpha')).toBe(true);
      expect(SEMVER_PATTERN.test('1.0.0-alpha.1')).toBe(true);
      expect(SEMVER_PATTERN.test('1.0.0+build.1')).toBe(true);
      expect(SEMVER_PATTERN.test('1.0.0-alpha+build')).toBe(true);
    });
    it('SEMVER_PATTERN rejects invalid semver', () => {
      expect(SEMVER_PATTERN.test('1')).toBe(false);
      expect(SEMVER_PATTERN.test('1.0')).toBe(false);
      expect(SEMVER_PATTERN.test('v1.0.0')).toBe(false);
      expect(SEMVER_PATTERN.test('')).toBe(false);
    });

    it('UUID_V4_PATTERN accepts valid UUID v4', () => {
      expect(UUID_V4_PATTERN.test(validUuidV4)).toBe(true);
      expect(UUID_V4_PATTERN.test(validUuidV4.toUpperCase())).toBe(true);
    });
    it('UUID_V4_PATTERN rejects invalid UUIDs', () => {
      expect(UUID_V4_PATTERN.test('not-a-uuid')).toBe(false);
      expect(UUID_V4_PATTERN.test('REDACTED')).toBe(false); // v1
      expect(UUID_V4_PATTERN.test('')).toBe(false);
    });
  });
});
