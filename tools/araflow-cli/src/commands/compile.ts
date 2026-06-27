/**
 * compile command — compiles a protocol source into an Execution Plan
 * and prints the plan + diagnostics.
 *
 * Equivalent to validate but goes all the way through IR + optimizer +
 * Execution Plan build, even when validation has warnings.
 */

import chalk from 'chalk';
import { ProtocolCompiler } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { formatWarnings, countBySeverity } from '../formatters/warnings';
import { formatPlan } from '../formatters/plan';
import { toJson } from '../formatters/json';

export interface CompileOptions {
  readonly filepath: string;
  readonly json?: boolean;
}

export const runCompile = async (opts: CompileOptions): Promise<number> => {
  const source = loadProtocolSource(opts.filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const result = compiler.compile(source);

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        ok: result.plan !== null,
        plan: result.plan,
        failures: result.failures,
        warnings: result.warnings,
        diagnostics: result.diagnostics,
        counts: {
          ...countBySeverity(result.failures),
          warnings: result.warnings.length,
        },
      }) + '\n',
    );
    return result.plan !== null ? 0 : 2;
  }

  if (result.plan === null) {
    process.stdout.write(chalk.red(`✗ Compilation failed for ${opts.filepath}\n\n`));
    process.stdout.write(formatWarnings(result.failures));
    return 2;
  }

  process.stdout.write(chalk.bold.green(`✓ Compiled ${opts.filepath}\n\n`));
  process.stdout.write(formatPlan(result.plan));

  process.stdout.write(chalk.bold('Diagnostics'));
  process.stdout.write('\n');
  process.stdout.write(chalk.gray('─'.repeat(60)));
  process.stdout.write('\n');
  const d = result.diagnostics;
  process.stdout.write(`  ${chalk.gray('parseTimeMs'.padEnd(24))} ${d.parseTimeMs.toFixed(2)}ms\n`);
  process.stdout.write(
    `  ${chalk.gray('validateTimeMs'.padEnd(24))} ${d.validateTimeMs.toFixed(2)}ms\n`,
  );
  process.stdout.write(
    `  ${chalk.gray('migrateTimeMs'.padEnd(24))} ${d.migrateTimeMs.toFixed(2)}ms\n`,
  );
  process.stdout.write(
    `  ${chalk.gray('buildIrTimeMs'.padEnd(24))} ${d.buildIrTimeMs.toFixed(2)}ms\n`,
  );
  process.stdout.write(
    `  ${chalk.gray('optimizeTimeMs'.padEnd(24))} ${d.optimizeTimeMs.toFixed(2)}ms\n`,
  );
  process.stdout.write(`  ${chalk.gray('lintTimeMs'.padEnd(24))} ${d.lintTimeMs.toFixed(2)}ms\n`);
  process.stdout.write(`  ${chalk.gray('totalTimeMs'.padEnd(24))} ${d.totalTimeMs.toFixed(2)}ms\n`);
  process.stdout.write(`  ${chalk.gray('passes'.padEnd(24))} ${d.optimizerPasses.join(', ')}\n\n`);

  if (result.warnings.length > 0) {
    process.stdout.write(formatWarnings(result.warnings));
  }
  if (result.failures.length > 0) {
    process.stdout.write(chalk.bold('Failures:\n'));
    process.stdout.write(formatWarnings(result.failures));
  }

  return 0;
};
