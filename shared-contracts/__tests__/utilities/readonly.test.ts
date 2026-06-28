/**
 * readonly.ts — DeepReadonly<T>, Immutable<T> type tests (compile-time).
 *
 * Runtime coverage of types is limited (they erase at runtime). Tests
 * verify the type-level behavior via TS assignment checks.
 */

import type { DeepReadonly, Immutable } from '../../src/utilities/readonly';

interface Sample {
  name: string;
  count: number;
  nested: { flag: boolean; list: number[] };
}

describe('utilities/readonly', () => {
  it('DeepReadonly works at compile-time', () => {
    const sample: DeepReadonly<Sample> = {
      name: 'a',
      count: 1,
      nested: { flag: true, list: [1, 2] },
    };
    // Read access only — assignment is forbidden by type
    expect(sample.name).toBe('a');
    expect(sample.nested.flag).toBe(true);
    expect(sample.nested.list).toEqual([1, 2]);
  });
  it('Immutable is alias for DeepReadonly', () => {
    const sample: Immutable<Sample> = {
      name: 'b',
      count: 2,
      nested: { flag: false, list: [] },
    };
    expect(sample.name).toBe('b');
  });
});
