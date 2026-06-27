/**
 * E2E integration test — full pipeline using all 4 engines.
 *
 * This is the proof that the Core works end-to-end.
 *
 * Pipeline under test:
 *   1. Read JSON file (load-source)
 *   2. Parse + validate + optimize (ProtocolCompiler)
 *   3. Run simulation (SimulationRuntime)
 *   4. Run real-time (TimerEngine + BreathEngine + ProtocolRuntime)
 *   5. Lint (ProtocolCompiler.warnings)
 *   6. Benchmark (timings)
 *
 * All four engines (Timer, Breath, Compiler, Runtime) are exercised.
 */

import { join } from 'node:path';
import { runValidate } from '../../src/commands/validate';
import { runCompile } from '../../src/commands/compile';
import { runSimulate } from '../../src/commands/simulate';
import { runLint } from '../../src/commands/lint';
import { runExplain } from '../../src/commands/explain';
import { runBenchmark } from '../../src/commands/benchmark';

const FIXTURE = (name: string): string => join(__dirname, '..', '..', 'fixtures', name);

describe('E2E — full Core integration', () => {
  it('runs all 5 read-only commands on box-breathing', async () => {
    expect(await runValidate({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runCompile({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runSimulate({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runLint({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runExplain({ filepath: FIXTURE('box-breathing.json') })).toBe(0);
    expect(await runBenchmark({ filepath: FIXTURE('box-breathing.json'), iterations: 1 })).toBe(0);
  }, 60_000);

  it('runs all 5 commands on 4-7-8', async () => {
    expect(await runValidate({ filepath: FIXTURE('four-seven-eight.json') })).toBe(0);
    expect(await runCompile({ filepath: FIXTURE('four-seven-eight.json') })).toBe(0);
    expect(await runSimulate({ filepath: FIXTURE('four-seven-eight.json') })).toBe(0);
    expect(await runLint({ filepath: FIXTURE('four-seven-eight.json') })).toBe(0);
    expect(await runExplain({ filepath: FIXTURE('four-seven-eight.json') })).toBe(0);
  }, 60_000);

  it('runs all 5 commands on diaphragmatic', async () => {
    expect(await runValidate({ filepath: FIXTURE('diaphragmatic.json') })).toBe(0);
    expect(await runCompile({ filepath: FIXTURE('diaphragmatic.json') })).toBe(0);
    expect(await runSimulate({ filepath: FIXTURE('diaphragmatic.json') })).toBe(0);
    expect(await runLint({ filepath: FIXTURE('diaphragmatic.json') })).toBe(0);
    expect(await runExplain({ filepath: FIXTURE('diaphragmatic.json') })).toBe(0);
  }, 60_000);

  it('runs all 5 commands on physiological-sigh', async () => {
    expect(await runValidate({ filepath: FIXTURE('physiological-sigh.json') })).toBe(0);
    expect(await runCompile({ filepath: FIXTURE('physiological-sigh.json') })).toBe(0);
    expect(await runSimulate({ filepath: FIXTURE('physiological-sigh.json') })).toBe(0);
    expect(await runLint({ filepath: FIXTURE('physiological-sigh.json') })).toBe(0);
    expect(await runExplain({ filepath: FIXTURE('physiological-sigh.json') })).toBe(0);
  }, 60_000);

  it('rejects invalid protocol across all read-only commands', async () => {
    // validate: returns 1 (blocking failures)
    expect(await runValidate({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(1);
    // compile: returns 2 (no plan)
    expect(await runCompile({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(2);
    // simulate: returns 2 (no plan)
    expect(await runSimulate({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(2);
    // lint: returns 0 (never blocks)
    expect(await runLint({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(0);
    // explain: returns 2
    expect(await runExplain({ filepath: FIXTURE('invalid-empty-phases.json') })).toBe(2);
  }, 60_000);
});
