/**
 * Tests for deterministic-json — strict, lossless, key-sorted JSON.
 */

import { parseDeterministic, stringifyDeterministic } from '@core/session-persistence';

describe('deterministic-json — stringify', () => {
  it('returns "null" for null', () => {
    expect(stringifyDeterministic(null)).toBe('null');
  });

  it('emits primitives verbatim', () => {
    expect(stringifyDeterministic(true)).toBe('true');
    expect(stringifyDeterministic(false)).toBe('false');
    expect(stringifyDeterministic(0)).toBe('0');
    expect(stringifyDeterministic(-3.14)).toBe('-3.14');
    expect(stringifyDeterministic('hello')).toBe('"hello"');
  });

  it('sorts object keys lexicographically', () => {
    const obj = { b: 1, a: 2, c: 3 };
    expect(stringifyDeterministic(obj)).toBe('{"a":2,"b":1,"c":3}');
  });

  it('omits undefined values', () => {
    const obj = { a: 1, b: undefined, c: 3 };
    expect(stringifyDeterministic(obj)).toBe('{"a":1,"c":3}');
  });

  it('serializes arrays preserving order', () => {
    expect(stringifyDeterministic([3, 1, 2])).toBe('[3,1,2]');
  });

  it('sorts nested object keys', () => {
    const obj = { z: { y: 1, x: 2 }, a: { c: 3, b: 4 } };
    expect(stringifyDeterministic(obj)).toBe('{"a":{"b":4,"c":3},"z":{"x":2,"y":1}}');
  });

  it('handles empty containers', () => {
    expect(stringifyDeterministic({})).toBe('{}');
    expect(stringifyDeterministic([])).toBe('[]');
  });

  it('is deterministic across runs', () => {
    const a = stringifyDeterministic({ z: 1, a: 2 });
    const b = stringifyDeterministic({ a: 2, z: 1 });
    expect(a).toBe(b);
  });

  it('rejects non-finite numbers', () => {
    expect(() => stringifyDeterministic(NaN)).toThrow(/non-finite/);
    expect(() => stringifyDeterministic(Infinity)).toThrow(/non-finite/);
  });

  it('rejects BigInt', () => {
    expect(() => stringifyDeterministic(BigInt(1))).toThrow(/BigInt/);
  });

  it('rejects circular references', () => {
    interface HasSelf {
      self: HasSelf;
    }
    const obj = {} as HasSelf;
    obj.self = obj;
    expect(() => stringifyDeterministic(obj)).toThrow(/circular/);
  });

  it('rejects unsupported types', () => {
    expect(() => stringifyDeterministic(new Map())).toThrow(/unsupported/);
  });

  it('does not lose precision for integers', () => {
    const s = stringifyDeterministic(Number.MAX_SAFE_INTEGER);
    expect(parseDeterministic<number>(s)).toBe(Number.MAX_SAFE_INTEGER);
  });

  it('does not lose precision for floats', () => {
    const s = stringifyDeterministic(0.1 + 0.2);
    expect(parseDeterministic<number>(s)).toBe(0.1 + 0.2);
  });
});

describe('deterministic-json — parse', () => {
  it('returns a frozen object', () => {
    const v = parseDeterministic<{ a: number }>('{"a":1}');
    expect(Object.isFrozen(v)).toBe(true);
  });

  it('deeply freezes nested objects', () => {
    const v = parseDeterministic<{ a: { b: number } }>('{"a":{"b":1}}');
    expect(Object.isFrozen(v.a)).toBe(true);
  });

  it('round-trips complex structures', () => {
    const input = { a: 1, b: [1, 2, 3], c: { d: 'x' } };
    const s = stringifyDeterministic(input);
    expect(parseDeterministic(s)).toEqual(input);
  });
});
