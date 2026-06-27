#!/usr/bin/env node
/**
 * cli — bin entry point. Parses argv via commander and dispatches.
 *
 * Exit codes:
 *   0 — success
 *   1 — validation/lint failure
 *   2 — compilation failure (no plan produced)
 *   3 — runtime failure (timeout, errored, cancelled)
 *
 * Errors that escape a command (uncaught exceptions) exit with 99.
 */

import { buildProgram } from './program';

const main = (): void => {
  const program = buildProgram();
  program.parseAsync(process.argv).catch((err: unknown) => {
    process.stderr.write(`✗ Fatal error: ${err instanceof Error ? err.message : String(err)}\n`);
    if (err instanceof Error && err.stack !== undefined) {
      process.stderr.write(`${err.stack}\n`);
    }
    process.exit(99);
  });
};

main();
