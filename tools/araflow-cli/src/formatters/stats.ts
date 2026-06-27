/**
 * stats — computes and formats protocol-level statistics.
 *
 * All stats are pure derivations from the plan or document; they do not
 * peek into engines.
 */

import chalk from 'chalk';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

export interface ProtocolStats {
  readonly cycles: number;
  readonly phasesPerCycle: number;
  readonly totalPhases: number;
  readonly totalDurationMs: number;
  readonly totalDurationSec: number;
  readonly avgPhaseMs: number;
  readonly avgPhaseSec: number;
  readonly breathsPerMinute: number;
  readonly phasesBreakdown: Readonly<Record<string, number>>;
}

export const computeStats = (plan: ProtocolExecutionPlan): ProtocolStats => {
  const totalDurationMs = plan.totalDuration as unknown as number;
  const totalDurationSec = totalDurationMs / 1000;
  const phasesPerCycle = plan.cycles > 0 ? plan.phases.length / plan.cycles : 0;
  const avgPhaseMs = plan.phases.length > 0 ? totalDurationMs / plan.phases.length : 0;

  // BPM = cycles per minute
  const breathsPerMinute = totalDurationSec > 0 ? (plan.cycles * 60) / totalDurationSec : 0;

  const breakdown: Record<string, number> = {};
  for (const p of plan.phases) {
    breakdown[p.phase] = (breakdown[p.phase] ?? 0) + 1;
  }

  return {
    cycles: plan.cycles,
    phasesPerCycle,
    totalPhases: plan.phases.length,
    totalDurationMs,
    totalDurationSec,
    avgPhaseMs,
    avgPhaseSec: avgPhaseMs / 1000,
    breathsPerMinute,
    phasesBreakdown: breakdown,
  };
};

export const formatStats = (stats: ProtocolStats): string => {
  const lines: string[] = [];
  lines.push(chalk.bold('Statistics'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(`  ${chalk.gray('cycles')}              ${stats.cycles}`);
  lines.push(`  ${chalk.gray('phases / cycle')}      ${stats.phasesPerCycle}`);
  lines.push(`  ${chalk.gray('total phases')}        ${stats.totalPhases}`);
  lines.push(`  ${chalk.gray('total duration')}      ${stats.totalDurationSec.toFixed(2)}s`);
  lines.push(`  ${chalk.gray('avg phase')}           ${stats.avgPhaseSec.toFixed(2)}s`);
  lines.push(`  ${chalk.gray('breaths / minute')}    ${stats.breathsPerMinute.toFixed(2)}`);
  lines.push(`  ${chalk.gray('phases breakdown')}`);
  for (const [phase, count] of Object.entries(stats.phasesBreakdown)) {
    lines.push(`    - ${phase.padEnd(20)} ${count}`);
  }
  lines.push('');
  return lines.join('\n');
};
