/**
 * json formatter tests.
 */

import { toJson } from '../../src/formatters/json';

describe('toJson', () => {
  it('serializes primitives', () => {
    expect(toJson(1)).toBe('1');
    expect(toJson('a')).toBe('"a"');
    expect(toJson(null)).toBe('null');
    expect(toJson(true)).toBe('true');
  });

  it('serializes objects with indentation', () => {
    const out = toJson({ a: 1, b: 'x' });
    expect(out).toContain('"a": 1');
    expect(out).toContain('"b": "x"');
    expect(out).toContain('\n');
  });

  it('serializes arrays', () => {
    expect(toJson([1, 2, 3])).toContain('1');
    expect(toJson([1, 2, 3])).toContain('3');
  });

  it('handles nested structures', () => {
    const out = toJson({ x: { y: [1, 2] } });
    expect(out).toContain('"y"');
    expect(out).toContain('1');
    expect(out).toContain('2');
  });
});
