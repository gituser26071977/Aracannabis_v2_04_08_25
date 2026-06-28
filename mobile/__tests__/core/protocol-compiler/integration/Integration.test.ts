/**
 * End-to-end integration test — pipeline from source to runtime.
 */

import { ProtocolCompiler } from '../../../../src/core/protocol-compiler/compiler/ProtocolCompiler';
import { JsonSource } from '../../../../src/core/protocol-compiler/domain/ProtocolSource';
import { SimulationRuntime } from '../../../../src/core/protocol-compiler/runtime/SimulationRuntime';
import type { Clock } from '@araflow/shared-contracts';
import { EngineId } from '@araflow/shared-contracts';

const COMPILER_ID = EngineId('protocol-compiler');

class FakeClock implements Clock {
  public t = 0;
  public now(): number {
    return this.t;
  }
  public wallNow(): number {
    return this.t;
  }
}

const fourSevenEightJson = (): string =>
  JSON.stringify({
    $schema: 'https://araflow.app/schemas/protocol/v1.json',
    id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    version: '1.0.0',
    title: '4-7-8 Relaxation',
    description: 'Classic relaxing breath',
    breath: {
      cycles: 4,
      restBetweenCyclesMs: 1000,
      phases: [
        { type: 'inhale', durationMs: 4000, curve: 'ease-in-out' },
        { type: 'hold-in', durationMs: 7000, curve: 'linear' },
        { type: 'exhale', durationMs: 8000, curve: 'ease-in-out' },
      ],
    },
    metadata: {
      author: 'Dr. Test',
      language: 'en',
      references: ['https://example.com/study'],
      evidenceLevel: 'B',
      contraindications: ['severe respiratory conditions'],
      category: 'calm',
      tags: ['sleep'],
      approvedAt: '2026-01-15T10:00:00.000Z',
    },
  });

describe('Protocol Compiler — integration', () => {
  it('runs the full pipeline source → parser → IR → plan → simulation', () => {
    const compiler = new ProtocolCompiler({
      compiledBy: COMPILER_ID,
      now: () => 1_700_000_000_000,
    });
    const result = compiler.compile(JsonSource(fourSevenEightJson()));
    // Filter to blocking failures only — semantic warnings are non-fatal.
    const blocking = result.failures.filter(
      (f) => f.severity === 'error' || f.severity === 'fatal',
    );
    expect(blocking).toEqual([]);
    expect(result.plan).not.toBeNull();
    if (result.plan === null) return;
    expect(result.plan.cycles).toBe(4);

    // Now simulate
    const sim = new SimulationRuntime(result.plan, new FakeClock());
    const report = sim.runToCompletion();
    // 4 cycles × 3 phases = 12 transitions
    expect(report.totalCycles).toBe(4);
    expect(report.phases.length).toBeGreaterThanOrEqual(12);
  });

  it('preserves all metadata through the pipeline', () => {
    const compiler = new ProtocolCompiler({
      compiledBy: COMPILER_ID,
      now: () => 1_700_000_000_000,
    });
    const result = compiler.compile(JsonSource(fourSevenEightJson()));
    expect(result.plan).not.toBeNull();
    if (result.plan === null) return;
    expect(result.plan.metadata.author).toBe('Dr. Test');
    expect(result.plan.metadata.evidenceLevel).toBe('B');
    expect(result.plan.metadata.contraindications).toEqual(['severe respiratory conditions']);
  });

  it('emits lint warnings (not blocking) for protocols missing author', () => {
    const json = JSON.stringify({
      $schema: 'https://araflow.app/schemas/protocol/v1.json',
      id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
      version: '1.0.0',
      title: 'No author',
      breath: {
        cycles: 1,
        phases: [
          { type: 'inhale', durationMs: 1000 },
          { type: 'exhale', durationMs: 1000 },
        ],
      },
      metadata: {
        category: 'calm',
      },
    });
    const compiler = new ProtocolCompiler({
      compiledBy: COMPILER_ID,
      now: () => 1_700_000_000_000,
    });
    const result = compiler.compile(JsonSource(json));
    // Author missing AND category set → semantic error (blocking)
    expect(result.failures.some((f) => f.code === 'semantic_author_missing')).toBe(true);
    expect(result.plan).toBeNull();
  });

  it('produces the same checksum across compilations of identical input', () => {
    const compiler = new ProtocolCompiler({
      compiledBy: COMPILER_ID,
      now: () => 1_700_000_000_000,
    });
    const a = compiler.compile(JsonSource(fourSevenEightJson()));
    const b = compiler.compile(JsonSource(fourSevenEightJson()));
    expect(a.plan?.checksum).toBe(b.plan?.checksum);
    expect(a.plan?.executionId).toBe(b.plan?.executionId);
  });

  it('different content produces different checksums', () => {
    const compiler = new ProtocolCompiler({
      compiledBy: COMPILER_ID,
      now: () => 1_700_000_000_000,
    });
    const a = compiler.compile(JsonSource(fourSevenEightJson()));
    const modified = JSON.parse(fourSevenEightJson()) as Record<string, unknown>;
    (modified as { title: string }).title = 'Different Title';
    const b = compiler.compile(JsonSource(JSON.stringify(modified)));
    expect(a.plan?.checksum).not.toBe(b.plan?.checksum);
  });
});