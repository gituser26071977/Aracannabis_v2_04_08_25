/**
 * validate command — runs only the validation stages of the compiler.
 *
 * Equivalent to `compile` but exits non-zero on validation failures
 * without trying to build a plan. Useful as a CI gate.
 */

import chalk from 'chalk';
import { ProtocolCompiler } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { formatWarnings, countBySeverity } from '../formatters/warnings';
import { toJson } from '../formatters/json';

export interface ValidateOptions {
  readonly filepath: string;
  readonly json?: boolean;
}

export const runValidate = async (opts: ValidateOptions): Promise<number> => {
  const source = loadProtocolSource(opts.filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const result = compiler.compile(source);

  const counts = countBySeverity(result.failures);
  const blocking = counts.fatal + counts.error;
  const ok = blocking === 0;

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        ok,
        filepath: opts.filepath,
        failures: result.failures,
        warnings: result.warnings,
        counts: {
          ...counts,
          blocking,
        },
      }) + '\n',
    );
    return ok ? 0 : 1;
  }

  if (ok) {
    process.stdout.write(chalk.bold.green(`✓ ${opts.filepath} is valid.\n\n`));
  } else {
    process.stdout.write(
      chalk.bold.red(`✗ ${opts.filepath} has ${blocking} blocking failure(s).\n\n`),
    );
  }

  if (result.failures.length > 0) {
    process.stdout.write(formatWarnings(result.failures));
  }
  if (result.warnings.length > 0) {
    process.stdout.write(chalk.bold('Lint warnings (non-blocking):\n'));
    process.stdout.write(formatWarnings(result.warnings));
  }

  return ok ? 0 : 1;
};
