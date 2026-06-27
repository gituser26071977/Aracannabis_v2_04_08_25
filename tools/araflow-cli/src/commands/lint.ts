/**
 * lint command — runs only the lint rules (warnings, non-blocking).
 *
 * Compile is required to obtain both the document and the plan
 * (the lint rules inspect both). Failures are reported but the
 * exit code is always 0 — lint never blocks.
 */

import chalk from 'chalk';
import { ProtocolCompiler } from '@core/protocol-compiler';
import { CLI_COMPILER_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { formatWarnings } from '../formatters/warnings';
import { toJson } from '../formatters/json';

export interface LintOptions {
  readonly filepath: string;
  readonly json?: boolean;
}

export const runLint = async (opts: LintOptions): Promise<number> => {
  const source = loadProtocolSource(opts.filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const result = compiler.compile(source);

  // If compilation failed, still emit any warnings the compiler
  // accumulated, plus parse-time warnings.
  const warnings = result.warnings;

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        filepath: opts.filepath,
        ok: result.plan !== null,
        warningCount: warnings.length,
        warnings,
      }) + '\n',
    );
    return 0; // lint never blocks
  }

  process.stdout.write(chalk.bold(`Lint ${opts.filepath}\n`));
  process.stdout.write(chalk.gray('─'.repeat(60)));
  process.stdout.write('\n');
  if (warnings.length === 0) {
    process.stdout.write(chalk.green('✓ No warnings.\n'));
  } else {
    process.stdout.write(formatWarnings(warnings));
  }
  return 0;
};
