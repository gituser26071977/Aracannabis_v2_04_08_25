/**
 * AraFlow CLI — public programmatic entry.
 *
 * Consumers (e.g. tests, future integrations) can `import { runProgram, ARAFLOW_CLI_VERSION } from '@araflow/cli'`
 * and call `runProgram(argv)` directly without spawning a child process.
 */

import { buildProgram, ARAFLOW_CLI_VERSION } from './program';

export { ARAFLOW_CLI_VERSION };
export { buildProgram };

/**
 * Runs the CLI with the given argv. Returns the exit code instead of
 * calling process.exit (testable). Internally uses the same builder
 * as the bin entry.
 */
export const runProgram = async (argv: readonly string[]): Promise<number> => {
  // commander accepts (node, script, ...argv). We synthesize fake node/script.
  const program = buildProgram();
  // Replace process.exit so commands return codes instead of killing the process
  const originalExit = process.exit;
  let exitCode = 0;
  process.exit = ((code?: number) => {
    exitCode = code ?? 0;
    // Throw to abort command flow; commander handles the throw internally.
    const e = new Error('__test_exit__');
    (e as Error & { code: number }).code = exitCode;
    throw e;
  }) as typeof process.exit;
  try {
    await program.parseAsync(['node', 'araflow', ...argv]);
  } catch (e) {
    if (e instanceof Error && e.message === '__test_exit__') {
      // expected
    } else if (e instanceof Error) {
      // IO/load errors thrown by commands (e.g. missing file) — treat as fatal (99)
      process.exit = originalExit;
      process.stderr.write(`araflow: ${e.message}\n`);
      return 99;
    }
  } finally {
    process.exit = originalExit;
  }
  return exitCode;
};
