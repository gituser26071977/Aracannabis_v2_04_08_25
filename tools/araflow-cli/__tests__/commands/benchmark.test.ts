/**
 * benchmark command tests.
 */

import { join } from 'node:path';
import { runBenchmark } from '../../src/commands/benchmark';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('runBenchmark', () => {
  it('returns 0 on valid protocol', async () => {
    const code = await runBenchmark({ filepath: FIXTURE('box-breathing.json') });
    expect(code).toBe(0);
  });

  it('prints all metric sections', async () => {
    const out = await captureStdout(() =>
      runBenchmark({ filepath: FIXTURE('box-breathing.json'), iterations: 2 }),
    );
    expect(out).toContain('Benchmark');
    expect(out).toContain('plan');
    expect(out).toContain('parse');
    expect(out).toContain('compile');
    expect(out).toContain('execute');
    expect(out).toContain('total');
    expect(out).toContain('peak heap delta');
    expect(out).toContain('cpu user');
    expect(out).toContain('drift');
  });

  it('emits JSON with aggregate and iteration data', async () => {
    const out = await captureStdout(() =>
      runBenchmark({ filepath: FIXTURE('box-breathing.json'), iterations: 3, json: true }),
    );
    const parsed = JSON.parse(out) as {
      aggregate: {
        iterations: number;
        parseMs: number;
        compileMs: number;
        executeMs: number;
        cycles: number;
        phases: number;
      };
      iterations: Array<{ parseMs: number }>;
      min: { parseMs: number };
      max: { parseMs: number };
    };
    expect(parsed.aggregate.iterations).toBe(3);
    expect(parsed.aggregate.parseMs).toBeGreaterThanOrEqual(0);
    expect(parsed.aggregate.cycles).toBe(4);
    expect(parsed.aggregate.phases).toBe(16);
    expect(parsed.iterations.length).toBe(3);
    expect(parsed.min.parseMs).toBeLessThanOrEqual(parsed.max.parseMs);
  });

  it('uses default iterations when not specified', async () => {
    const out = await captureStdout(() =>
      runBenchmark({ filepath: FIXTURE('box-breathing.json'), json: true }),
    );
    const parsed = JSON.parse(out) as { aggregate: { iterations: number } };
    expect(parsed.aggregate.iterations).toBe(5); // default
  });

  it('runs on smaller protocols', async () => {
    const out = await captureStdout(() =>
      runBenchmark({ filepath: FIXTURE('physiological-sigh.json'), iterations: 1 }),
    );
    expect(out).toContain('Benchmark');
  });

  it('handles invalid protocol gracefully', async () => {
    const code = await runBenchmark({ filepath: FIXTURE('invalid-empty-phases.json') });
    // Returns 0 (benchmark doesn't fail on compile errors, just reports 0 phases)
    expect(code).toBe(0);
  });
});
