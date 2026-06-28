/**
 * option.ts — Option<T>, Some, None, helpers.
 */

import {
  Some,
  None,
  isSome,
  isNone,
  mapOption,
  flatMapOption,
  unwrapOptionOr,
  zip2,
  firstSome,
} from '../../src/patterns/option';

describe('patterns/option', () => {
  describe('Some / None', () => {
    it('Some produces frozen object', () => {
      const o = Some(42);
      expect(o).toEqual({ some: true, value: 42 });
      expect(Object.isFrozen(o)).toBe(true);
    });
    it('None produces frozen object', () => {
      const o = None<number>();
      expect(o).toEqual({ some: false });
      expect(Object.isFrozen(o)).toBe(true);
    });
  });

  describe('isSome / isNone', () => {
    it('isSome narrows correctly', () => {
      const o = Some(1);
      if (isSome(o)) {
        expect(o.value).toBe(1);
      } else {
        fail('expected some');
      }
    });
    it('isNone narrows correctly', () => {
      const o: Option<number> = None();
      if (isNone(o)) {
        expect(o.some).toBe(false);
      } else {
        fail('expected none');
      }
    });
  });

  describe('mapOption', () => {
    it('maps value on Some', () => {
      expect(mapOption(Some(2), (v) => v * 3)).toEqual(Some(6));
    });
    it('returns None on None', () => {
      expect(mapOption(None<number>(), (v) => v * 3)).toEqual(None());
    });
  });

  describe('flatMapOption', () => {
    it('chains Some → Some', () => {
      expect(flatMapOption(Some(2), (v) => Some(v * 3))).toEqual(Some(6));
    });
    it('chains Some → None', () => {
      expect(flatMapOption(Some(2), () => None<number>())).toEqual(None());
    });
    it('preserves None', () => {
      expect(flatMapOption(None<number>(), () => Some(99))).toEqual(None());
    });
  });

  describe('unwrapOptionOr', () => {
    it('returns value on Some', () => {
      expect(unwrapOptionOr(Some(42), 0)).toBe(42);
    });
    it('returns fallback on None', () => {
      expect(unwrapOptionOr(None<number>(), 0)).toBe(0);
    });
  });

  describe('zip2', () => {
    it('zips two Some', () => {
      const z = zip2(Some(1), Some('a'));
      expect(z).toEqual(Some([1, 'a'] as const));
    });
    it('returns None when first None', () => {
      expect(zip2(None<number>(), Some('a'))).toEqual(None());
    });
    it('returns None when second None', () => {
      expect(zip2(Some(1), None<string>())).toEqual(None());
    });
    it('returns None when both None', () => {
      expect(zip2(None<number>(), None<string>())).toEqual(None());
    });
  });

  describe('firstSome', () => {
    it('returns first Some', () => {
      expect(firstSome([None(), Some(2), Some(3)])).toEqual(Some(2));
    });
    it('returns None when all None', () => {
      expect(firstSome([None<number>(), None<number>()])).toEqual(None());
    });
    it('returns None for empty list', () => {
      expect(firstSome([])).toEqual(None());
    });
  });
});

import type { Option } from '../../src/patterns/option';
