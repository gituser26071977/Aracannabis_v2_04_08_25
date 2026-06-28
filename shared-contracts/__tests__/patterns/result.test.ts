/**
 * result.ts — Result<T,E>, Ok, Err, helpers.
 */

import {
  Ok,
  Err,
  isOk,
  isErr,
  mapResult,
  mapError,
  flatMapResult,
  unwrap,
  unwrapOr,
  allResults,
} from '../../src/patterns/result';

describe('patterns/result', () => {
  describe('Ok / Err', () => {
    it('Ok produces frozen object', () => {
      const r = Ok(42);
      expect(r).toEqual({ ok: true, value: 42 });
      expect(Object.isFrozen(r)).toBe(true);
    });
    it('Err produces frozen object', () => {
      const r = Err('fail');
      expect(r).toEqual({ ok: false, error: 'fail' });
      expect(Object.isFrozen(r)).toBe(true);
    });
  });

  describe('isOk / isErr', () => {
    it('isOk narrows correctly', () => {
      const r = Ok(1);
      if (isOk(r)) {
        expect(r.value).toBe(1);
      } else {
        fail('expected ok');
      }
    });
    it('isErr narrows correctly', () => {
      const r = Err('e');
      if (isErr(r)) {
        expect(r.error).toBe('e');
      } else {
        fail('expected err');
      }
    });
  });

  describe('mapResult', () => {
    it('maps value when ok', () => {
      expect(mapResult(Ok(2), (v) => v * 3)).toEqual(Ok(6));
    });
    it('preserves error when err', () => {
      expect(mapResult(Err('e') as Result<number, string>, (v) => v * 3)).toEqual(Err('e'));
    });
  });

  describe('mapError', () => {
    it('maps error when err', () => {
      expect(mapError(Err('e') as Result<number, string>, (e) => `${e}!`)).toEqual(Err('e!'));
    });
    it('preserves value when ok', () => {
      expect(mapError(Ok(1) as Result<number, string>, (e) => `${e}!`)).toEqual(Ok(1));
    });
  });

  describe('flatMapResult', () => {
    it('chains ok operations', () => {
      const r = flatMapResult(Ok(2), (v) => Ok(v * 3));
      expect(r).toEqual(Ok(6));
    });
    it('chains ok → err', () => {
      const r = flatMapResult(Ok(2), () => Err('fail'));
      expect(r).toEqual(Err('fail'));
    });
    it('short-circuits on err', () => {
      const r = flatMapResult(Err('e') as Result<number, string>, () => Ok(99));
      expect(r).toEqual(Err('e'));
    });
  });

  describe('unwrap', () => {
    it('returns value on ok', () => {
      expect(unwrap(Ok(42))).toBe(42);
    });
    it('throws Error on err string', () => {
      expect(() => unwrap(Err('boom'))).toThrow('boom');
    });
    it('throws wrapped Error on err object', () => {
      class CustomError extends Error {
        public constructor(msg: string) {
          super(msg);
          this.name = 'Custom';
        }
      }
      expect(() => unwrap(Err(new CustomError('inner')))).toThrow(CustomError);
    });
  });

  describe('unwrapOr', () => {
    it('returns value on ok', () => {
      expect(unwrapOr(Ok(42), 0)).toBe(42);
    });
    it('returns fallback on err', () => {
      expect(unwrapOr(Err('e'), 0)).toBe(0);
    });
  });

  describe('allResults', () => {
    it('returns Ok([]) for empty list', () => {
      const r = allResults([]);
      expect(r).toEqual(Ok([]));
    });
    it('returns Ok with all values when all ok', () => {
      const r = allResults([Ok(1), Ok(2), Ok(3)]);
      expect(r).toEqual(Ok([1, 2, 3]));
    });
    it('returns first Err when any err', () => {
      const r = allResults([Ok(1), Err('first'), Err('second')]);
      expect(r).toEqual(Err('first'));
    });
    it('handles mixed types with same error type', () => {
      const r = allResults<number, string>([Ok(1), Ok(2)]);
      expect(isOk(r)).toBe(true);
      if (isOk(r)) expect(r.value).toEqual([1, 2]);
    });
  });
});

import type { Result } from '../../src/patterns/result';
