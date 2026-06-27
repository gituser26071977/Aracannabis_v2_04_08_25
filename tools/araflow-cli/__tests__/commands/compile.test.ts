/**
 * compile command tests.
 */

import { join } from 'node:path';
import { runCompile } from '../../src/commands/compile';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('runCompile', () => {
  it('returns 0 on valid protocol', async () => {
    const code = await runCompile({ filepath: FIXTURE('box-breathing.json') });
    expect(code).toBe(0);
  });

  it('returns 2 on invalid protocol', async () => {
    const code = await runCompile({ filepath: FIXTURE('invalid-empty-phases.json') });
    expect(code).toBe(2);
  });

  it('prints plan details', async () => {
    const out = await captureStdout(() =>
      runCompile({ filepath: FIXTURE('four-seven-eight.json') }),
    );
    expect(out).toContain('Compiled');
    expect(out).toContain('Protocol Execution Plan');
    expect(out).toContain('Cycles & Duration');
    expect(out).toContain('Phases');
  });

  it('prints diagnostics', async () => {
    const out = await captureStdout(() => runCompile({ filepath: FIXTURE('box-breathing.json') }));
    expect(out).toContain('Diagnostics');
    expect(out).toContain('parseTimeMs');
    expect(out).toContain('totalTimeMs');
    expect(out).toContain('passes');
  });

  it('emits JSON output', async () => {
    const out = await captureStdout(() =>
      runCompile({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as {
      ok: boolean;
      plan: { cycles: number };
      diagnostics: { totalTimeMs: number };
    };
    expect(parsed.ok).toBe(true);
    expect(parsed.plan.cycles).toBe(4);
    expect(parsed.diagnostics.totalTimeMs).toBeGreaterThanOrEqual(0);
  });

  it('emits JSON failures', async () => {
    const out = await captureStdout(() =>
      runCompile({ filepath: FIXTURE('invalid-empty-phases.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { ok: boolean };
    expect(parsed.ok).toBe(false);
  });
});
