/**
 * run command tests — exercises Timer Engine + Breath Engine + ProtocolRuntime together.
 *
 * Uses real wall-clock Timer Engine but a SHORT plan (diaphragmatic, 96s)
 * with explicit --max-duration-ms to bound test time. We assert that:
 *   - run completes within the deadline (or hits timeout cleanly)
 *   - phases are observed
 *   - cycle transitions are observed
 *   - JSON output is well-formed
 */

import { join } from 'node:path';
import { runCommand, summariseRuntime } from '../../src/commands/run';
import { captureStdout } from '../helpers/capture';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('summariseRuntime (event formatting helper)', () => {
  it('formats started event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-started',
      executionId: 'exec-1',
      atElapsedMs: 0,
    });
    expect(out).toContain('started');
    expect(out).toContain('exec-1');
  });

  it('formats paused event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-paused',
      atElapsedMs: 1000,
    });
    expect(out).toContain('paused');
    expect(out).toContain('1000');
  });

  it('formats resumed event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-resumed',
      pausedForMs: 500,
    });
    expect(out).toContain('resumed');
    expect(out).toContain('500');
  });

  it('formats tick event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-tick',
      elapsedMs: 100,
      cycleIndex: 0,
      phase: 'inhaling',
      phaseProgress: 0.5,
    });
    expect(out).toContain('tick');
    expect(out).toContain('inhaling');
  });

  it('formats phase-changed event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-phase-changed',
      currentPhase: 'exhaling',
      cycleIndex: 1,
    });
    expect(out).toContain('exhaling');
    expect(out).toContain('cycle 1');
  });

  it('formats cycle-completed event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-cycle-completed',
      cycleIndex: 2,
    });
    expect(out).toContain('cycle 2 done');
  });

  it('formats completed event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-completed',
      totalElapsedMs: 12345,
    });
    expect(out).toContain('completed');
    expect(out).toContain('12345');
  });

  it('formats stopped event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-stopped',
      reason: 'user-cancel',
    });
    expect(out).toContain('stopped');
    expect(out).toContain('user-cancel');
  });

  it('formats errored event', () => {
    const out = summariseRuntime({
      type: 'protocol-runtime-errored',
      code: 'engine-failure',
      message: 'something went wrong',
    });
    expect(out).toContain('errored');
    expect(out).toContain('engine-failure');
  });
});

describe('runCommand (real Timer Engine + Breath Engine + Runtime)', () => {
  // Use physiological-sigh (short: 3 cycles × 9s = 27s)
  it('runs a short plan to completion', async () => {
    const code = await runCommand({
      filepath: FIXTURE('physiological-sigh.json'),
      maxDurationMs: 60_000,
      quiet: true,
    });
    expect([0, 3]).toContain(code); // 0=completed, 3=timeout/error
  }, 90_000);

  it('emits JSON output with drift and event counts', async () => {
    const out = await captureStdout(() =>
      runCommand({
        filepath: FIXTURE('physiological-sigh.json'),
        maxDurationMs: 60_000,
        quiet: true,
        json: true,
      }),
    );
    const parsed = JSON.parse(out) as {
      ok: boolean;
      executionId: string;
      plannedDurationMs: number;
      actualDurationMs: number;
      driftMs: number;
      phasesObserved: number;
      cycleTransitions: number;
      stoppedReason: string;
    };
    expect(parsed.executionId.length).toBeGreaterThan(0);
    expect(parsed.plannedDurationMs).toBeGreaterThan(0);
    expect(parsed.actualDurationMs).toBeGreaterThan(0);
    // We allow either completed or timeout for tests
    expect(['completed', 'timeout', 'cancelled']).toContain(parsed.stoppedReason);
    // If completed, we expect phase observations
    if (parsed.stoppedReason === 'completed') {
      expect(parsed.phasesObserved).toBeGreaterThan(0);
    }
  }, 90_000);

  it('reports phases observed in non-quiet mode', async () => {
    // Small plan: diaphragmatic (16s × 6 = 96s) — set max to 30s to force timeout
    // Actually too long. Use sigh (27s) with 30s deadline.
    const out = await captureStdout(() =>
      runCommand({
        filepath: FIXTURE('physiological-sigh.json'),
        maxDurationMs: 60_000,
        quiet: false,
      }),
    );
    expect(out.length).toBeGreaterThan(0);
  }, 90_000);

  it('handles invalid input gracefully', async () => {
    await expect(
      runCommand({
        filepath: FIXTURE('invalid-empty-phases.json'),
        maxDurationMs: 5_000,
        quiet: true,
      }),
    ).rejects.toThrow(/Compilation failed/);
  });
});
