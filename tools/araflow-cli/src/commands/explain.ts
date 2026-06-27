/**
 * explain command — compiles a plan AND runs SimulationRuntime to
 * produce a complete explanation: plan + timeline + stats + warnings.
 *
 * This is the "show me everything" command — the most thorough output
 * the CLI produces.
 */

import chalk from 'chalk';
import { ProtocolCompiler, SimulationRuntime } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { createSystemClock } from '../util/clock';
import { formatPlan } from '../formatters/plan';
import { formatSimulationTimeline } from '../formatters/timeline';
import { formatStats, computeStats } from '../formatters/stats';
import { formatSummary, type SessionSummary } from '../formatters/summary';
import { formatWarnings, countBySeverity } from '../formatters/warnings';
import { toJson } from '../formatters/json';

export interface ExplainOptions {
  readonly filepath: string;
  readonly json?: boolean;
  readonly tickMs?: number;
}

export const runExplain = async (opts: ExplainOptions): Promise<number> => {
  const source = loadProtocolSource(opts.filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const result = compiler.compile(source);

  if (result.plan === null) {
    if (opts.json === true) {
      process.stdout.write(
        toJson({
          ok: false,
          filepath: opts.filepath,
          failures: result.failures,
          warnings: result.warnings,
        }) + '\n',
      );
    } else {
      process.stdout.write(chalk.red(`✗ Cannot explain: compilation failed.\n\n`));
      process.stdout.write(formatWarnings(result.failures));
    }
    return 2;
  }

  const clock = createSystemClock();
  const sim = new SimulationRuntime(result.plan, clock, {
    ...(opts.tickMs !== undefined ? { tickMs: opts.tickMs } : {}),
  });
  const report = sim.runToCompletion();
  const stats = computeStats(result.plan);

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        ok: true,
        filepath: opts.filepath,
        plan: result.plan,
        simulation: report,
        stats,
        warnings: result.warnings,
        counts: countBySeverity(result.failures),
      }) + '\n',
    );
    return 0;
  }

  process.stdout.write(chalk.bold.green(`✓ Explanation for ${opts.filepath}\n\n`));
  process.stdout.write(formatPlan(result.plan));
  process.stdout.write(formatStats(stats));
  process.stdout.write(formatSimulationTimeline(report.phases, report.cycles));

  const summary: SessionSummary = {
    executionId: result.plan.executionId,
    title: 'explanation',
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
