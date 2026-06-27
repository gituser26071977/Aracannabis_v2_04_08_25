/**
 * explain command tests.
 */

import { join } from 'node:path';
import { runExplain } from '../../src/commands/explain';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('runExplain', () => {
  it('returns 0 on valid protocol', async () => {
    const code = await runExplain({ filepath: FIXTURE('box-breathing.json') });
    expect(code).toBe(0);
  });

  it('returns 2 on invalid protocol', async () => {
    const code = await runExplain({ filepath: FIXTURE('invalid-empty-phases.json') });
    expect(code).toBe(2);
  });

  it('renders plan + timeline + stats + summary', async () => {
    const out = await captureStdout(() => runExplain({ filepath: FIXTURE('box-breathing.json') }));
    expect(out).toContain('Protocol Execution Plan');
    expect(out).toContain('Timeline');
    expect(out).toContain('Statistics');
    expect(out).toContain('Session Summary');
  });

  it('emits JSON with full payload', async () => {
    const out = await captureStdout(() =>
      runExplain({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as {
      ok: boolean;
      plan: { cycles: number };
      simulation: { totalPhases: number };
      stats: { cycles: number; totalPhases: number };
    };
    expect(parsed.ok).toBe(true);
    expect(parsed.plan.cycles).toBe(4);
    expect(parsed.simulation.totalPhases).toBe(16);
    expect(parsed.stats.cycles).toBe(4);
  });

  it('emits JSON failure on invalid', async () => {
    const out = await captureStdout(() =>
      runExplain({ filepath: FIXTURE('invalid-empty-phases.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { ok: boolean; failures: unknown[] };
    expect(parsed.ok).toBe(false);
    expect(parsed.failures.length).toBeGreaterThan(0);
  });
});
