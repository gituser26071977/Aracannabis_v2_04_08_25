/**
 * summary — formats a one-shot final summary block at the end of a run.
 */

import chalk from 'chalk';

export interface SessionSummary {
  readonly executionId: string;
  readonly title: string;
  readonly cycles: number;
  readonly totalPhases: number;
  readonly plannedDurationMs: number;
  readonly actualDurationMs: number;
  readonly driftMs: number;
  readonly phasesObserved: number;
  readonly cycleTransitionsObserved: number;
  readonly completedNaturally: boolean;
  readonly stoppedReason: 'completed' | 'cancelled' | 'errored' | 'timeout';
}

const padLeft = (s: string, n: number): string =>
  s.length >= n ? s : ' '.repeat(n - s.length) + s;

export const formatSummary = (summary: SessionSummary): string => {
  const lines: string[] = [];
  lines.push(chalk.bold('Session Summary'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(`  ${chalk.gray('executionId')}        ${summary.executionId}`);
  lines.push(`  ${chalk.gray('title')}              ${summary.title}`);
  lines.push(`  ${chalk.gray('cycles')}             ${summary.cycles}`);
  lines.push(
    `  ${chalk.gray('phases observed')}    ${summary.phasesObserved} / ${summary.totalPhases}`,
  );
  lines.push(`  ${chalk.gray('cycle transitions')}  ${summary.cycleTransitionsObserved}`);
  lines.push(
    `  ${chalk.gray('planned duration')}   ${(summary.plannedDurationMs / 1000).toFixed(2)}s`,
  );
  lines.push(
    `  ${chalk.gray('actual duration')}    ${(summary.actualDurationMs / 1000).toFixed(2)}s`,
  );
  const driftColor =
    Math.abs(summary.driftMs) < 100
      ? chalk.green
      : Math.abs(summary.driftMs) < 500
        ? chalk.yellow
        : chalk.red;
  lines.push(
    `  ${chalk.gray('drift')}              ${driftColor(`${padLeft(summary.driftMs.toFixed(0), 6)} ms`)}`,
  );
  lines.push(`  ${chalk.gray('final state')}        ${summary.stoppedReason}`);
  if (summary.completedNaturally) {
    lines.push('');
    lines.push(chalk.green.bold('  ✓ Session completed successfully.'));
  } else {
    lines.push('');
    lines.push(chalk.yellow(`  ! Session ended via ${summary.stoppedReason}.`));
  }
  lines.push('');
  return lines.join('\n');
};
