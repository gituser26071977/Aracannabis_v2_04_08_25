/**
 * timeline — formats a sequence of phase transitions (or runtime events)
 * as a human-readable timeline. Used by `simulate` and `run`.
 */

import chalk from 'chalk';
import type { SimulationPhaseRecord, SimulationCycleRecord } from '@core/protocol-compiler';

const fmtTime = (ms: number): string => `${(ms / 1000).toFixed(2).padStart(7)}s`;

export const formatSimulationTimeline = (
  phases: readonly SimulationPhaseRecord[],
  cycles: readonly SimulationCycleRecord[],
): string => {
  const lines: string[] = [];
  lines.push(chalk.bold('Timeline (Simulation)'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(
    `  ${chalk.gray('startAt')}  ${chalk.gray('endAt')}  ${chalk.gray('duration')}  ${chalk.gray('cycle')}  ${chalk.gray('phase')}`,
  );
  for (const p of phases) {
    const start = fmtTime(p.startedAtMs);
    const end = fmtTime(p.endedAtMs);
    const dur = `${(p.durationMs / 1000).toFixed(2)}s`;
    lines.push(
      `  ${start}  ${end}  ${dur.padStart(8)}  ${padLeft(String(p.cycleIndex), 5)}  ${p.phase}`,
    );
  }
  lines.push('');
  lines.push(chalk.bold(`Cycles (${cycles.length}):`));
  for (const c of cycles) {
    lines.push(
      `  cycle ${padLeft(String(c.cycleIndex), 3)}  duration=${(c.cycleDurationMs / 1000).toFixed(2)}s  phases=${c.phases.length}`,
    );
  }
  lines.push('');
  return lines.join('\n');
};

const padLeft = (s: string, n: number): string =>
  s.length >= n ? s : ' '.repeat(n - s.length) + s;

export type RuntimeEventLine = {
  readonly t: number;
  readonly stream: 'protocol' | 'breath' | 'timer';
  readonly summary: string;
};

export const formatRuntimeEventStream = (events: readonly RuntimeEventLine[]): string => {
  const lines: string[] = [];
  lines.push(chalk.bold('Runtime Event Stream'));
  lines.push(chalk.gray('─'.repeat(60)));
  for (const e of events) {
    const t = fmtTime(e.t);
    const tag =
      e.stream === 'protocol'
        ? chalk.cyan('[protocol]')
        : e.stream === 'breath'
          ? chalk.green('[breath]')
          : chalk.gray('[timer]');
    lines.push(`  ${t}  ${tag} ${e.summary}`);
  }
  lines.push('');
  return lines.join('\n');
};
