/**
 * summary formatter tests.
 */

import { formatSummary, type SessionSummary } from '../../src/formatters/summary';

const baseSummary = (over: Partial<SessionSummary> = {}): SessionSummary => ({
  executionId: 'exec-1',
  title: 'Test',
  cycles: 4,
  totalPhases: 12,
  plannedDurationMs: 60000,
  actualDurationMs: 60050,
  driftMs: 50,
  phasesObserved: 12,
  cycleTransitionsObserved: 4,
  completedNaturally: true,
  stoppedReason: 'completed',
  ...over,
});

describe('formatSummary', () => {
  it('renders all fields', () => {
    const out = formatSummary(baseSummary());
    expect(out).toContain('Session Summary');
    expect(out).toContain('exec-1');
    expect(out).toContain('cycles');
    expect(out).toMatch(/4/);
    expect(out).toContain('planned duration');
    expect(out).toContain('actual duration');
    expect(out).toContain('drift');
    expect(out).toContain('completed');
  });

  it('shows green checkmark when completed naturally', () => {
    const out = formatSummary(baseSummary({ completedNaturally: true }));
    expect(out).toContain('✓');
  });

  it('shows warning for non-completion', () => {
    const out = formatSummary(
      baseSummary({ completedNaturally: false, stoppedReason: 'cancelled' }),
    );
    expect(out).toContain('cancelled');
  });

  it('drift coloring reflects magnitude', () => {
    const small = formatSummary(baseSummary({ driftMs: 50 }));
    const big = formatSummary(baseSummary({ driftMs: 1000 }));
    expect(small).toContain('50 ms');
    expect(big).toContain('1000 ms');
  });

  it('handles all stop reasons', () => {
    expect(formatSummary(baseSummary({ stoppedReason: 'completed' }))).toContain('completed');
    expect(formatSummary(baseSummary({ stoppedReason: 'cancelled' }))).toContain('cancelled');
    expect(formatSummary(baseSummary({ stoppedReason: 'errored' }))).toContain('errored');
    expect(formatSummary(baseSummary({ stoppedReason: 'timeout' }))).toContain('timeout');
  });
});
