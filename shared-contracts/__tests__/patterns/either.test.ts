/**
 * either.ts — Either<L,R>, Left, Right, helpers.
 */

import {
  Left,
  Right,
  isLeft,
  isRight,
  mapLeft,
  mapRight,
  unwrapEither,
} from '../../src/patterns/either';

describe('patterns/either', () => {
  describe('Left / Right', () => {
    it('Left produces frozen object', () => {
      const e = Left('err');
      expect(e).toEqual({ left: 'err' });
      expect(Object.isFrozen(e)).toBe(true);
    });
    it('Right produces frozen object', () => {
      const e = Right(42);
      expect(e).toEqual({ right: 42 });
      expect(Object.isFrozen(e)).toBe(true);
    });
  });

  describe('isLeft / isRight', () => {
    it('isLeft narrows', () => {
      const e: Either<string, number> = Left('x');
      if (isLeft(e)) {
        expect(e.left).toBe('x');
      } else {
        fail('expected left');
      }
    });
    it('isRight narrows', () => {
      const e: Either<string, number> = Right(1);
      if (isRight(e)) {
        expect(e.right).toBe(1);
      } else {
        fail('expected right');
      }
    });
  });

  describe('mapLeft', () => {
    it('maps left when left', () => {
      expect(mapLeft(Left(1), (l) => l * 2)).toEqual(Left(2));
    });
    it('preserves right', () => {
      expect(mapLeft(Right('r') as Either<number, string>, () => 99)).toEqual(Right('r'));
    });
  });

  describe('mapRight', () => {
    it('maps right when right', () => {
      expect(mapRight(Right(2), (r) => r * 3)).toEqual(Right(6));
    });
    it('preserves left', () => {
      expect(mapRight(Left('l') as Either<string, number>, () => 99)).toEqual(Left('l'));
    });
  });

  describe('unwrapEither', () => {
    it('returns right value when right', () => {
      expect(unwrapEither(Right(42), 0)).toBe(42);
    });
    it('returns default when left', () => {
      expect(unwrapEither(Left('e'), 0)).toBe(0);
    });
  });
});

import type { Either } from '../../src/patterns/either';
