/**
 * program — builds the commander program and registers all 7 sub-commands.
 *
 * Keeping program builder separate from `cli.ts` makes it testable:
 *   `buildProgram()` can be called from Jest without invoking process.
 */

import { Command } from 'commander';
import { runValidate } from './commands/validate';
import { runCompile } from './commands/compile';
import { runSimulate } from './commands/simulate';
import { runCommand as runRunCommand } from './commands/run';
import { runLint } from './commands/lint';
import { runBenchmark } from './commands/benchmark';
import { runExplain } from './commands/explain';

export const ARAFLOW_CLI_VERSION = '0.1.0';

export const buildProgram = (): Command => {
  const program = new Command();
  program
    .name('araflow')
    .description(
      'AraFlow Core Integration Harness — validate, compile, simulate, run, lint, benchmark, and explain protocols using the four frozen Core engines.',
    )
    .version(ARAFLOW_CLI_VERSION, '-V, --version', 'output the version number');

  program
    .command('validate <file>')
    .description('Validate a protocol (Schema + Semantic + Compatibility)')
    .option('--json', 'output JSON instead of human-readable text')
    .action(async (file: string, options: { json?: boolean }) => {
      const code = await runValidate({
        filepath: file,
        ...(options.json === true ? { json: true } : {}),
      });
      process.exit(code);
    });

  program
    .command('compile <file>')
    .description('Compile a protocol to an Execution Plan')
    .option('--json', 'output JSON instead of human-readable text')
    .action(async (file: string, options: { json?: boolean }) => {
      const code = await runCompile({
        filepath: file,
        ...(options.json === true ? { json: true } : {}),
      });
      process.exit(code);
    });

  program
    .command('simulate <file>')
    .description('Simulate a plan without the Timer Engine')
    .option('--json', 'output JSON instead of human-readable text')
    .option('--tick-ms <ms>', 'simulation tick granularity in ms (default 100)', (v) => Number(v))
    .action(async (file: string, options: { json?: boolean; tickMs?: number }) => {
      const code = await runSimulate({
        filepath: file,
        ...(options.json === true ? { json: true } : {}),
        ...(options.tickMs !== undefined ? { tickMs: options.tickMs } : {}),
      });
      process.exit(code);
    });

  program
    .command('run <file>')
    .description('Run a plan with the real Timer Engine + Breath Engine')
    .option('--json', 'output JSON instead of human-readable text')
    .option('--max-duration-ms <ms>', 'safety timeout in ms (default 5min)', (v) => Number(v))
    .option('--quiet', 'suppress event stream output')
    .action(
      async (
        file: string,
        options: { json?: boolean; maxDurationMs?: number; quiet?: boolean },
      ) => {
        const code = await runRunCommand({
          filepath: file,
          ...(options.json === true ? { json: true } : {}),
          ...(options.maxDurationMs !== undefined ? { maxDurationMs: options.maxDurationMs } : {}),
          ...(options.quiet === true ? { quiet: true } : {}),
        });
        process.exit(code);
      },
    );

  program
    .command('lint <file>')
    .description('Run lint rules (warnings only, never blocking)')
    .option('--json', 'output JSON instead of human-readable text')
    .action(async (file: string, options: { json?: boolean }) => {
      const code = await runLint({
        filepath: file,
        ...(options.json === true ? { json: true } : {}),
      });
      process.exit(code);
    });

  program
    .command('benchmark <file>')
    .description('Measure parse, compile, execute, memory, CPU, drift')
    .option('--json', 'output JSON instead of human-readable text')
    .option('--iterations <n>', 'number of iterations to average', (v) => Number(v))
    .option('--tick-ms <ms>', 'simulation tick granularity in ms', (v) => Number(v))
    .action(
      async (file: string, options: { json?: boolean; iterations?: number; tickMs?: number }) => {
        const code = await runBenchmark({
          filepath: file,
          ...(options.json === true ? { json: true } : {}),
          ...(options.iterations !== undefined ? { iterations: options.iterations } : {}),
          ...(options.tickMs !== undefined ? { tickMs: options.tickMs } : {}),
        });
        process.exit(code);
      },
    );

  program
    .command('explain <file>')
    .description('Show plan + timeline + warnings + stats + summary')
    .option('--json', 'output JSON instead of human-readable text')
    .option('--tick-ms <ms>', 'simulation tick granularity in ms (default 100)', (v) => Number(v))
    .action(async (file: string, options: { json?: boolean; tickMs?: number }) => {
      const code = await runExplain({
        filepath: file,
        ...(options.json === true ? { json: true } : {}),
        ...(options.tickMs !== undefined ? { tickMs: options.tickMs } : {}),
      });
      process.exit(code);
    });

  return program;
};
