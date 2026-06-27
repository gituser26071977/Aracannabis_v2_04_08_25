/**
 * simulate command tests.
 */

import { join } from 'node:path';
import { runSimulate } from '../../src/commands/simulate';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('runSimulate', () => {
  it('returns 0 on valid protocol', async () => {
    const code = await runSimulate({ filepath: FIXTURE('box-breathing.json') });
    expect(code).toBe(0);
  });

  it('returns 2 on invalid protocol', async () => {
    const code = await runSimulate({ filepath: FIXTURE('invalid-empty-phases.json') });
    expect(code).toBe(2);
  });

  it('produces correct phase count (4 phases × 4 cycles = 16 for box)', async () => {
    const out = await captureStdout(() => runSimulate({ filepath: FIXTURE('box-breathing.json') }));
    expect(out).toContain('Simulated');
    // Box breathing has 4 phases per cycle × 4 cycles = 16 total
    // (simulation reports `phases` count)
    expect(out).toContain('16');
  });

  it('respects tickMs option', async () => {
    const out = await captureStdout(() =>
      runSimulate({ filepath: FIXTURE('box-breathing.json'), tickMs: 50 }),
    );
    expect(out).toContain('Simulated');
  });

  it('emits valid JSON with --json', async () => {
    const out = await captureStdout(() =>
      runSimulate({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as {
      ok: boolean;
      plan: { cycles: number; executionId: string };
      simulation: { totalPhases: number; totalCycles: number };
    };
    expect(parsed.ok).toBe(true);
    expect(parsed.plan.cycles).toBe(4);
    expect(parsed.simulation.totalCycles).toBe(4);
    expect(parsed.simulation.totalPhases).toBe(16);
  });

  it('emits JSON failures on invalid input', async () => {
    const out = await captureStdout(() =>
      runSimulate({ filepath: FIXTURE('invalid-empty-phases.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { ok: boolean; failures: unknown[] };
    expect(parsed.ok).toBe(false);
    expect(parsed.failures.length).toBeGreaterThan(0);
  });

  it('runs 4-7-8 with 3 phases × 4 cycles = 12 transitions', async () => {
    const out = await captureStdout(() =>
      runSimulate({ filepath: FIXTURE('four-seven-eight.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { simulation: { totalPhases: number } };
    expect(parsed.simulation.totalPhases).toBe(12);
  });
});
