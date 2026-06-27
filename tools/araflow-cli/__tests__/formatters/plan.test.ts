/**
 * plan formatter tests.
 */

import { formatPlan } from '../../src/formatters/plan';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import { Duration } from '@araflow/shared-contracts';

const fakePlan = (): ProtocolExecutionPlan => ({
  executionId: 'exec-1' as never,
  protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FAV' as never,
  version: '1.0.0' as never,
  schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
  compilerVersion: '1.0.0',
  title: 'Test Plan',
  metadata: {
    author: 'Ara',
    language: 'en',
    references: ['ref-1'],
    evidenceLevel: 'B',
    contraindications: ['x'],
    category: 'calm',
    tags: ['sleep'],
    approvedAt: '2026-01-01T00:00:00.000Z' as never,
  },
  phases: [
    {
      index: 0 as never,
      phase: 'inhaling',
      duration: Duration(4000),
      curve: 'ease-in-out',
    },
    {
      index: 1 as never,
      phase: 'exhaling',
      duration: Duration(4000),
      curve: 'ease-in-out',
    },
  ],
  cycles: 2,
  totalDuration: Duration(8000),
  totalCycleDuration: Duration(4000),
  compiledAt: '2026-01-01T00:00:00.000Z' as never,
  compiledBy: 'cli-harness' as never,
  checksum: 'fnv1a:abcd1234',
});

describe('formatPlan', () => {
  it('renders header', () => {
    const out = formatPlan(fakePlan());
    expect(out).toContain('Protocol Execution Plan');
    expect(out).toContain('exec-1');
    expect(out).toContain('fnv1a:abcd1234');
  });

  it('renders cycles & duration', () => {
    const out = formatPlan(fakePlan());
    expect(out).toContain('Cycles & Duration');
    expect(out).toContain('cycles');
    expect(out).toContain('totalDuration');
  });

  it('renders phase table', () => {
    const out = formatPlan(fakePlan());
    expect(out).toContain('Phases');
    expect(out).toContain('inhaling');
    expect(out).toContain('exhaling');
    expect(out).toContain('ease-in-out');
  });

  it('renders metadata', () => {
    const out = formatPlan(fakePlan());
    expect(out).toContain('Metadata');
    expect(out).toContain('Ara');
    expect(out).toContain('ref-1');
    expect(out).toContain('sleep');
    expect(out).toContain('2026-01-01');
  });

  it('omits optional metadata fields when absent', () => {
    const plan = fakePlan();
    plan.metadata = { references: [], contraindications: [], tags: [] };
    const out = formatPlan(plan);
    expect(out).toContain('Metadata');
    expect(out).not.toContain('author');
    expect(out).not.toContain('language');
  });
});
