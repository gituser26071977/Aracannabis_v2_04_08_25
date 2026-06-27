/**
 * warnings formatter tests.
 */

import { formatWarnings, countBySeverity } from '../../src/formatters/warnings';
import type { Failure } from '@araflow/shared-contracts';

const f = (over: Partial<Failure>): Failure => ({
  code: 'test_code',
  message: 'test message',
  severity: 'warn',
  ...over,
});

describe('formatWarnings', () => {
  it('returns green checkmark when no failures', () => {
    const out = formatWarnings([]);
    expect(out).toContain('No warnings');
  });

  it('renders code and message', () => {
    const out = formatWarnings([f({ code: 'lint_x', message: 'thing happened' })]);
    expect(out).toContain('lint_x');
    expect(out).toContain('thing happened');
  });

  it('includes path when present', () => {
    const out = formatWarnings([f({ path: 'breath.phases[0]' })]);
    expect(out).toContain('breath.phases[0]');
  });

  it('renders context entries', () => {
    const out = formatWarnings([f({ context: { cycles: 100 } })]);
    expect(out).toContain('cycles');
    expect(out).toContain('100');
  });

  it('uses different colors per severity', () => {
    const out = formatWarnings([
      f({ severity: 'fatal' }),
      f({ severity: 'error' }),
      f({ severity: 'warn' }),
      f({ severity: 'info' }),
    ]);
    expect(out).toContain('FATAL');
    expect(out).toContain('ERROR');
    expect(out).toContain('WARN');
    expect(out).toContain('INFO');
  });

  it('handles unknown severity gracefully', () => {
    // Force unknown value via cast (test only)
    const out = formatWarnings([f({ severity: 'unknown' as unknown as Failure['severity'] })]);
    expect(out).toContain('test_code');
  });
});

describe('countBySeverity', () => {
  it('returns all zeros on empty input', () => {
    expect(countBySeverity([])).toEqual({ fatal: 0, error: 0, warn: 0, info: 0 });
  });

  it('counts each severity bucket', () => {
    const out = countBySeverity([
      f({ severity: 'fatal' }),
      f({ severity: 'fatal' }),
      f({ severity: 'error' }),
      f({ severity: 'warn' }),
      f({ severity: 'info' }),
    ]);
    expect(out).toEqual({ fatal: 2, error: 1, warn: 1, info: 1 });
  });
});
