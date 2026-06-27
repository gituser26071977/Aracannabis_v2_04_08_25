/**
 * index programmatic entry tests.
 */

import { runProgram, ARAFLOW_CLI_VERSION } from '../src';

describe('runProgram (programmatic CLI)', () => {
  it('returns 0 for --help', async () => {
    const code = await runProgram(['--help']);
    expect(code).toBe(0);
  }, 10_000);

  it('returns 0 for --version', async () => {
    const code = await runProgram(['--version']);
    expect(code).toBe(0);
  }, 10_000);

  it('returns 2 for invalid protocol file', async () => {
    const code = await runProgram(['simulate', '/nope/missing.json']);
    // simulate returns 2 on compile failure, or 99 on read failure
    expect([2, 99]).toContain(code);
  }, 10_000);

  it('returns 0 for valid simulate', async () => {
    const code = await runProgram(['simulate', 'fixtures/box-breathing.json']);
    expect(code).toBe(0);
  }, 30_000);

  it('returns 0 for valid validate', async () => {
    const code = await runProgram(['validate', 'fixtures/box-breathing.json']);
    expect(code).toBe(0);
  }, 30_000);

  it('returns 0 for valid compile', async () => {
    const code = await runProgram(['compile', 'fixtures/box-breathing.json']);
    expect(code).toBe(0);
  }, 30_000);

  it('returns 0 for lint (never blocks)', async () => {
    const code = await runProgram(['lint', 'fixtures/box-breathing.json']);
    expect(code).toBe(0);
  }, 30_000);

  it('re-exports version', () => {
    expect(ARAFLOW_CLI_VERSION).toBe('0.1.0');
  });
});
