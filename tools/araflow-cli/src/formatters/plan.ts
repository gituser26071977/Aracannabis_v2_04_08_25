/**
 * plan — formats a ProtocolExecutionPlan as a human-readable block.
 *
 * Sections:
 *   - Identity (executionId, sourceProtocolId, version)
 *   - Checksum + format version
 *   - Cycle / duration summary
 *   - Phase table
 *   - Metadata
 */

import chalk from 'chalk';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

const cycleDurationSec = (ms: unknown): string => `${(Number(ms) / 1000).toFixed(2)}s`;
const totalDurationSec = (ms: unknown): string => `${(Number(ms) / 1000).toFixed(2)}s`;

const padRight = (s: string, n: number): string =>
  s.length >= n ? s : s + ' '.repeat(n - s.length);
const padLeft = (s: string, n: number): string =>
  s.length >= n ? s : ' '.repeat(n - s.length) + s;

export const formatPlan = (plan: ProtocolExecutionPlan): string => {
  const lines: string[] = [];

  lines.push(chalk.bold('Protocol Execution Plan'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(`  ${chalk.gray('executionId')}      ${plan.executionId}`);
  lines.push(`  ${chalk.gray('protocolId')}       ${plan.protocolId}`);
  lines.push(`  ${chalk.gray('version')}          ${plan.version}`);
  lines.push(`  ${chalk.gray('schemaUri')}        ${plan.schemaUri}`);
  lines.push(`  ${chalk.gray('compilerVersion')}  ${plan.compilerVersion}`);
  lines.push(`  ${chalk.gray('checksum')}         ${plan.checksum}`);
  lines.push(`  ${chalk.gray('compiledAt')}       ${plan.compiledAt}`);
  lines.push(`  ${chalk.gray('compiledBy')}       ${plan.compiledBy}`);
  lines.push('');

  lines.push(chalk.bold('Cycles & Duration'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(`  ${chalk.gray('cycles')}              ${plan.cycles}`);
  lines.push(`  ${chalk.gray('totalCycleDuration')}  ${cycleDurationSec(plan.totalCycleDuration)}`);
  lines.push(`  ${chalk.gray('totalDuration')}       ${totalDurationSec(plan.totalDuration)}`);
  lines.push('');

  const phasesPerCycle = plan.cycles > 0 ? plan.phases.length / plan.cycles : 0;
  lines.push(chalk.bold('Phases'));
  lines.push(chalk.gray('─'.repeat(60)));
  lines.push(
    `  ${chalk.gray(padRight('idx', 6))}${chalk.gray(padRight('cycle', 8))}${chalk.gray(padRight('phase', 18))}${chalk.gray(padRight('duration', 12))}${chalk.gray('curve')}`,
  );
  for (const p of plan.phases) {
    const idxNum = p.index as unknown as number;
    const cycNum = phasesPerCycle > 0 ? Math.floor(idxNum / phasesPerCycle) : 0;
    const idx = padLeft(String(idxNum), 4);
    const cyc = padLeft(String(cycNum), 6);
    const ph = padRight(p.phase, 16);
    const dur = padLeft(cycleDurationSec(p.duration), 10);
    lines.push(`  ${idx}  ${cyc}  ${ph}  ${dur}  ${p.curve}`);
  }
  lines.push('');

  lines.push(chalk.bold('Metadata'));
  lines.push(chalk.gray('─'.repeat(60)));
  const md = plan.metadata;
  if (md.author !== undefined) lines.push(`  ${chalk.gray('author')}            ${md.author}`);
  if (md.language !== undefined) lines.push(`  ${chalk.gray('language')}          ${md.language}`);
  if (md.evidenceLevel !== undefined)
    lines.push(`  ${chalk.gray('evidenceLevel')}     ${md.evidenceLevel}`);
  if (md.category !== undefined) lines.push(`  ${chalk.gray('category')}          ${md.category}`);
  if (md.references.length > 0) {
    lines.push(`  ${chalk.gray('references')}`);
    for (const ref of md.references) lines.push(`    - ${ref}`);
  }
  if (md.contraindications.length > 0) {
    lines.push(`  ${chalk.gray('contraindications')}`);
    for (const c of md.contraindications) lines.push(`    - ${c}`);
  }
  if (md.tags.length > 0) lines.push(`  ${chalk.gray('tags')}              ${md.tags.join(', ')}`);
  if (md.approvedAt !== undefined)
    lines.push(`  ${chalk.gray('approvedAt')}        ${md.approvedAt}`);
  lines.push('');

  return lines.join('\n');
};
