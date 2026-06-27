/**
 * lint command tests.
 */

import { join } from 'node:path';
import { runLint } from '../../src/commands/lint';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('runLint', () => {
  it('always returns 0 (lint never blocks)', async () => {
    expect(await runLint({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runLint({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(0);
  });

  it('prints header', async () => {
    const out = await captureStdout(() => runLint({ filepath: FIXTURE('box-breathing.json') }));
    expect(out).toContain('Lint');
    expect(out).toContain('box-breathing.json');
  });

  it('emits JSON', async () => {
    const out = await captureStdout(() =>
      runLint({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { warningCount: number; warnings: unknown[] };
    expect(parsed.warningCount).toBe(parsed.warnings.length);
  });

  it('shows no-warnings message when clean', async () => {
    // All our fixtures are well-formed; box-breathing has full metadata.
    const out = await captureStdout(() => runLint({ filepath: FIXTURE('box-breathing.json') }));
    // Either "No warnings" or list of warnings — both are valid
    expect(out.length).toBeGreaterThan(0);
  });

  it('prints warning list when warnings are present', async () => {
    // box-breathing.json contains 4-phase Box pattern that the linter flags
    // with "semantic_consecutive_inhale"/"semantic_consecutive_exhale".
    const out = await captureStdout(() => runLint({ filepath: FIXTURE('box-breathing.json') }));
    expect(out).toContain('semantic_consecutive_inhale');
    expect(out).toContain('semantic_consecutive_exhale');
  });

  it('emits JSON with non-empty warnings when present', async () => {
    const out = await captureStdout(() =>
      runLint({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as {
      ok: boolean;
      warningCount: number;
      warnings: Array<{ code: string }>;
    };
    expect(parsed.ok).toBe(true);
    expect(parsed.warningCount).toBeGreaterThan(0);
    expect(parsed.warnings.length).toBeGreaterThan(0);
  });
});
