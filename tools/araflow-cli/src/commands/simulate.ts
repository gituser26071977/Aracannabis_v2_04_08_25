/**
 * simulate command — runs a plan through SimulationRuntime.
 *
 * No Timer Engine, no real time. Pure deterministic walk-through.
 *
 * Pipeline:
 *   1. Load JSON file as ProtocolSource
 *   2. Compile via ProtocolCompiler (validate + optimize + plan)
 *   3. If compile fails → print failures and exit non-zero
 *   4. Run SimulationRuntime.runToCompletion()
 *   5. Print timeline, cycles, summary (or JSON if --json)
 */

import chalk from 'chalk';
import { ProtocolCompiler, SimulationRuntime } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { createSystemClock } from '../util/clock';
import { formatWarnings } from '../formatters/warnings';
import { formatSimulationTimeline } from '../formatters/timeline';
import { formatSummary, type SessionSummary } from '../formatters/summary';
import { toJson } from '../formatters/json';

export interface SimulateOptions {
  readonly filepath: string;
  readonly json?: boolean;
  readonly tickMs?: number;
}

export const runSimulate = async (opts: SimulateOptions): Promise<number> => {
  const source = loadProtocolSource(opts.filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const result = compiler.compile(source);

  if (result.plan === null) {
    if (opts.json === true) {
      process.stdout.write(
        toJson({
          ok: false,
          failures: result.failures,
          warnings: result.warnings,
        }) + '\n',
      );
    } else {
      process.stdout.write(chalk.red(`✗ Compilation failed for ${opts.filepath}\n\n`));
      process.stdout.write(formatWarnings(result.failures));
    }
    return 2;
  }

  const clock = createSystemClock();
  const sim = new SimulationRuntime(result.plan, clock, {
    ...(opts.tickMs !== undefined ? { tickMs: opts.tickMs } : {}),
  });
  const report = sim.runToCompletion();

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        ok: true,
        plan: {
          executionId: result.plan.executionId,
          cycles: result.plan.cycles,
          totalDurationMs: result.plan.totalDuration as unknown as number,
          checksum: result.plan.checksum,
        },
        warnings: result.warnings,
        simulation: {
          executionId: report.executionId,
          totalCycles: report.totalCycles,
          totalPhases: report.totalPhases,
          totalDurationMs: report.totalDurationMs,
          cycles: report.cycles,
          phases: report.phases,
          checksum: report.checksum,
          startedAt: report.startedAt,
          completedAt: report.completedAt,
        },
      }) + '\n',
    );
    return 0;
  }

  process.stdout.write(chalk.bold.green(`✓ Simulated ${opts.filepath}\n\n`));
  process.stdout.write(
    `  ${chalk.gray('executionId')}  ${result.plan.executionId}\n` +
      `  ${chalk.gray('cycles')}       ${result.plan.cycles}\n` +
      `  ${chalk.gray('phases')}       ${report.totalPhases}\n` +
      `  ${chalk.gray('duration')}     ${(report.totalDurationMs / 1000).toFixed(2)}s\n` +
      `  ${chalk.gray('checksum')}     ${report.checksum}\n\n`,
  );
  process.stdout.write(formatSimulationTimeline(report.phases, report.cycles));

  const summary: SessionSummary = {
    executionId: result.plan.executionId,
    title: 'simulation',
    cycles: result.plan.cycles,
    totalPhases: report.totalPhases,
    plannedDurationMs: result.plan.totalDuration as unknown as number,
    actualDurationMs: report.totalDurationMs,
    driftMs: 0,
    phasesObserved: report.totalPhases,
    cycleTransitionsObserved: report.cycles.length,
    completedNaturally: true,
    stoppedReason: 'completed',
  };
  process.stdout.write(formatSummary(summary));

  if (result.warnings.length > 0) {
    process.stdout.write(formatWarnings(result.warnings));
  }

  return 0;
};
