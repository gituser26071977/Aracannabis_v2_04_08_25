/**
 * program builder tests.
 */

import { buildProgram, ARAFLOW_CLI_VERSION } from '../src/program';

describe('buildProgram', () => {
  it('exposes version constant', () => {
    expect(ARAFLOW_CLI_VERSION).toBe('0.1.0');
  });

  it('builds a commander program', () => {
    const program = buildProgram();
    expect(program.name()).toBe('araflow');
    expect(program.description()).toContain('Core Integration Harness');
  });

  it('registers all 7 sub-commands', () => {
    const program = buildProgram();
    const names = program.commands.map((c) => c.name());
    expect(names).toContain('validate');
    expect(names).toContain('compile');
    expect(names).toContain('simulate');
    expect(names).toContain('run');
    expect(names).toContain('lint');
    expect(names).toContain('benchmark');
    expect(names).toContain('explain');
  });
});
