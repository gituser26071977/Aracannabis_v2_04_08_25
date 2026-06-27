/**
 * load-source tests.
 */

import { loadProtocolSource } from '../../src/io/load-source';
import { join } from 'node:path';

const FIXTURES = join(__dirname, '..', '..', 'fixtures');

describe('loadProtocolSource', () => {
  it('loads a valid JSON file', () => {
    const src = loadProtocolSource(join(FIXTURES, 'box-breathing.json'));
    expect(src.format).toBe('json');
    expect(src.raw.length).toBeGreaterThan(0);
    expect(src.origin).toContain('box-breathing.json');
  });

  it('throws AppError on missing file', () => {
    expect(() => loadProtocolSource(join(FIXTURES, 'does-not-exist.json'))).toThrow(
      /Could not read protocol file/,
    );
  });

  it('throws AppError on empty file', () => {
    expect(() => loadProtocolSource('/dev/null')).toThrow(/empty/i);
  });
});
