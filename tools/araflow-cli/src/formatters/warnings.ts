/**
 * warnings — formats a list of Failure objects as a human-readable
 * block. Used by validate, lint, explain, and compile commands.
 */

import chalk from 'chalk';
import type { Failure } from '@araflow/shared-contracts';

const severityColor = (sev: Failure['severity']): ((s: string) => string) => {
  switch (sev) {
    case 'fatal':
      return chalk.bgRed.white;
    case 'error':
      return chalk.red;
    case 'warn':
      return chalk.yellow;
    case 'info':
      return chalk.cyan;
    default:
      return chalk.gray;
  }
};

const severityLabel = (sev: Failure['severity']): string => sev.toUpperCase().padEnd(5);

export const formatWarnings = (failures: readonly Failure[]): string => {
  if (failures.length === 0) {
    return chalk.green('✓ No warnings or failures.\n');
  }
  const lines: string[] = [];
  lines.push(chalk.bold(`Issues (${failures.length}):`));
  lines.push('');
  for (const f of failures) {
    const paint = severityColor(f.severity);
    const header = paint(`  [${severityLabel(f.severity)}] ${f.code}`);
    lines.push(header);
    if (f.path !== undefined) {
      lines.push(chalk.gray(`    at ${f.path}`));
    }
    lines.push(`    ${f.message}`);
    if (f.context !== undefined && Object.keys(f.context).length > 0) {
      for (const [key, value] of Object.entries(f.context)) {
        lines.push(chalk.gray(`    ${key}: ${JSON.stringify(value)}`));
      }
    }
  }
  lines.push('');
  return lines.join('\n');
};

export const countBySeverity = (
  failures: readonly Failure[],
): { fatal: number; error: number; warn: number; info: number } => {
  let fatal = 0;
  let error = 0;
  let warn = 0;
  let info = 0;
  for (const f of failures) {
    if (f.severity === 'fatal') fatal += 1;
    else if (f.severity === 'error') error += 1;
    else if (f.severity === 'warn') warn += 1;
    else if (f.severity === 'info') info += 1;
  }
  return { fatal, error, warn, info };
};
