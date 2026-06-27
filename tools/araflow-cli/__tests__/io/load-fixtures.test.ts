/**
 * load-fixtures tests.
 */

import { discoverFixtures } from '../../src/io/load-fixtures';
import { join } from 'node:path';

const FIXTURES = join(__dirname, '..', '..', 'fixtures');

describe('discoverFixtures', () => {
  it('returns sorted JSON paths', () => {
    const found = discoverFixtures(FIXTURES);
    expect(found.length).toBeGreaterThanOrEqual(5);
    expect(found.every((p) => p.endsWith('.json'))).toBe(true);
    // Sorted
    const sorted = [...found].sort();
    expect(found).toEqual(sorted);
  });

  it('includes all 5 known fixtures', () => {
    const found = discoverFixtures(FIXTURES);
    expect(found.some((p) => p.includes('box-breathing'))).toBe(true);
    expect(found.some((p) => p.includes('four-seven-eight'))).toBe(true);
    expect(found.some((p) => p.includes('diaphragmatic'))).toBe(true);
    expect(found.some((p) => p.includes('physiological-sigh'))).toBe(true);
    expect(found.some((p) => p.includes('invalid-empty-phases'))).toBe(true);
  });

  it('returns empty array for empty dir', () => {
    const tmpDir = join(FIXTURES, '__nonexistent__');
    expect(() => discoverFixtures(tmpDir)).toThrow();
  });
});
