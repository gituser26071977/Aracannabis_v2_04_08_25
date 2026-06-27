/**
 * benchmark command — measures parse, compile, execute (simulation),
 * peak memory, and CPU/drift for a protocol.
 *
 * Methodology:
 *   - parseMs: time to load JSON file from disk
 *   - compileMs: time spent in ProtocolCompiler.compile()
 *   - executeMs: time spent in SimulationRuntime.runToCompletion()
 *   - peakMemoryDeltaKb: heapUsed before vs after full pipeline
 *   - cpuUserMs / cpuSystemMs: process.cpuUsage() difference
 *   - driftMs: (real elapsed) - (planned duration) — drift between
 *     wall-clock execution and the plan's declared duration
 *
 * Drift is always 0 for simulation (it uses injected Clock), but we
 * still compute it for API consistency.
 */

import chalk from 'chalk';
import { ProtocolCompiler, SimulationRuntime } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { createSystemClock, memoryUsageBytes } from '../util/clock';
import { toJson } from '../formatters/json';

export interface BenchmarkOptions {
  readonly filepath: string;
  readonly json?: boolean;
  readonly iterations?: number;
  readonly tickMs?: number;
}

export interface BenchmarkReport {
  readonly filepath: string;
  readonly iterations: number;
  readonly parseMs: number;
  readonly compileMs: number;
  readonly executeMs: number;
  readonly totalMs: number;
  readonly peakMemoryDeltaKb: number;
  readonly cpuUserMs: number;
  readonly cpuSystemMs: number;
  readonly driftMs: number;
  readonly plannedDurationMs: number;
  readonly cycles: number;
  readonly phases: number;
}

const measureOne = (filepath: string, tickMs: number | undefined): BenchmarkReport => {
  const memBefore = memoryUsageBytes();
  const cpuBefore = process.cpuUsage();
  const wallStart = process.hrtime.bigint();

  const parseStart = process.hrtime.bigint();
  const source = loadProtocolSource(filepath);
  const parseEnd = process.hrtime.bigint();
  const parseMs = Number(parseEnd - parseStart) / 1_000_000;

  const compileStart = process.hrtime.bigint();
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const compileResult = compiler.compile(source);
  const compileEnd = process.hrtime.bigint();
  const compileMs = Number(compileEnd - compileStart) / 1_000_000;

  let executeMs = 0;
  let driftMs = 0;
  let cycles = 0;
  let phases = 0;
  let plannedDurationMs = 0;

  if (compileResult.plan !== null) {
    cycles = compileResult.plan.cycles;
    plannedDurationMs = compileResult.plan.totalDuration as unknown as number;
    const executeStart = process.hrtime.bigint();
    const sim = new SimulationRuntime(compileResult.plan, createSystemClock(), {
      ...(tickMs !== undefined ? { tickMs } : {}),
    });
    const simReport = sim.runToCompletion();
    const executeEnd = process.hrtime.bigint();
    executeMs = Number(executeEnd - executeStart) / 1_000_000;
    phases = simReport.totalPhases;
    driftMs = executeMs - plannedDurationMs;
  }

  const wallEnd = process.hrtime.bigint();
  const totalMs = Number(wallEnd - wallStart) / 1_000_000;
  const memAfter = memoryUsageBytes();
  const cpuAfter = process.cpuUsage(cpuBefore);

  return {
    filepath,
    iterations: 1,
    parseMs,
    compileMs,
    executeMs,
    totalMs,
    peakMemoryDeltaKb: Math.round((memAfter - memBefore) / 1024),
    cpuUserMs: Math.round(cpuAfter.user / 1000),
    cpuSystemMs: Math.round(cpuAfter.system / 1000),
    driftMs,
    plannedDurationMs,
    cycles,
    phases,
  };
};

export const runBenchmark = async (opts: BenchmarkOptions): Promise<number> => {
  const iterations = Math.max(1, opts.iterations ?? 5);
  const reports: BenchmarkReport[] = [];
  for (let i = 0; i < iterations; i += 1) {
    reports.push(measureOne(opts.filepath, opts.tickMs));
  }

  const sum = (key: keyof BenchmarkReport): number =>
    reports.reduce((acc, r) => acc + (r[key] as number), 0);
  const avg = (key: keyof BenchmarkReport): number => sum(key) / reports.length;
  const min = (key: keyof BenchmarkReport): number =>
    Math.min(...reports.map((r) => r[key] as number));
  const max = (key: keyof BenchmarkReport): number =>
    Math.max(...reports.map((r) => r[key] as number));

  const aggregate: BenchmarkReport = {
    filepath: opts.filepath,
    iterations,
    parseMs: round(avg('parseMs')),
    compileMs: round(avg('compileMs')),
    executeMs: round(avg('executeMs')),
    totalMs: round(avg('totalMs')),
    peakMemoryDeltaKb: round(max('peakMemoryDeltaKb')),
    cpuUserMs: round(avg('cpuUserMs')),
    cpuSystemMs: round(avg('cpuSystemMs')),
    driftMs: round(avg('driftMs')),
    plannedDurationMs: reports[0]?.plannedDurationMs ?? 0,
    cycles: reports[0]?.cycles ?? 0,
    phases: reports[0]?.phases ?? 0,
  };

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        aggregate,
        iterations: reports.map((r) => ({
          parseMs: r.parseMs,
          compileMs: r.compileMs,
          executeMs: r.executeMs,
          totalMs: r.totalMs,
          memoryKb: r.peakMemoryDeltaKb,
          cpuUserMs: r.cpuUserMs,
          cpuSystemMs: r.cpuSystemMs,
        })),
        min: {
          parseMs: round(min('parseMs')),
          compileMs: round(min('compileMs')),
          executeMs: round(min('executeMs')),
          totalMs: round(min('totalMs')),
        },
        max: {
          parseMs: round(max('parseMs')),
          compileMs: round(max('compileMs')),
          executeMs: round(max('executeMs')),
          totalMs: round(max('totalMs')),
        },
      }) + '\n',
    );
    return 0;
  }

  process.stdout.write(chalk.bold(`Benchmark ${opts.filepath} (${iterations} iterations)\n`));
  process.stdout.write(chalk.gray('─'.repeat(60)));
  process.stdout.write('\n');
  process.stdout.write(
    `  ${chalk.gray('plan')}              ${aggregate.cycles} cycles × ${aggregate.phases} phases\n`,
  );
  process.stdout.write(
    `  ${chalk.gray('planned duration')}  ${(aggregate.plannedDurationMs / 1000).toFixed(2)}s\n`,
  );
  process.stdout.write('\n');
  process.stdout.write(chalk.bold('Average timings (ms):\n'));
  process.stdout.write(`  ${chalk.gray('parse')}             ${aggregate.parseMs.toFixed(2)}\n`);
  process.stdout.write(`  ${chalk.gray('compile')}           ${aggregate.compileMs.toFixed(2)}\n`);
  process.stdout.write(`  ${chalk.gray('execute')}           ${aggregate.executeMs.toFixed(2)}\n`);
  process.stdout.write(`  ${chalk.gray('total')}             ${aggregate.totalMs.toFixed(2)}\n`);
  process.stdout.write('\n');
  process.stdout.write(chalk.bold('Resources:\n'));
  process.stdout.write(`  ${chalk.gray('peak heap delta')}   ${aggregate.peakMemoryDeltaKb} KB\n`);
  process.stdout.write(`  ${chalk.gray('cpu user')}          ${aggregate.cpuUserMs} ms\n`);
  process.stdout.write(`  ${chalk.gray('cpu system')}        ${aggregate.cpuSystemMs} ms\n`);
  process.stdout.write('\n');
  process.stdout.write(chalk.bold('Drift:\n'));
  process.stdout.write(
    `  ${chalk.gray('drift (simulation)')} ${aggregate.driftMs.toFixed(2)} ms\n`,
  );
  process.stdout.write('\n');
  return 0;
};

const round = (n: number): number => Math.round(n * 100) / 100;
