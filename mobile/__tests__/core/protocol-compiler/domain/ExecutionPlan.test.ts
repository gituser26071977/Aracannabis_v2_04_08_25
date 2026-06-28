/**
 * ExecutionPlan — builder and version constants.
 */

import {
  PROTOCOL_COMPILER_VERSION,
  PROTOCOL_PLAN_FORMAT_VERSION,
  ExecutionId,
  buildExecutionPlan,
} from '../../../../src/core/protocol-compiler/domain/ExecutionPlan';
import { ProtocolId } from '@araflow/shared-contracts';

describe('ExecutionPlan', () => {
  it('exposes compiler version 1.0.0', () => {
    expect(PROTOCOL_COMPILER_VERSION).toBe('1.0.0');
  });

  it('exposes plan format version 1.0.0', () => {
    expect(PROTOCOL_PLAN_FORMAT_VERSION).toBe('1.0.0');
  });

  describe('ExecutionId', () => {
    it('builds a branded ExecutionId from a string', () => {
      const id = ExecutionId('exec-abc');
      expect(id).toBe('exec-abc');
    });
  });

  describe('buildExecutionPlan', () => {
    it('builds a frozen plan', () => {
      const plan = buildExecutionPlan({
        executionId: ExecutionId('exec-1'),
        protocolId: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
        version: '1.0.0' as never,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
        compilerVersion: '1.0.0',
        title: 'Test',
        metadata: {
          references: [],
          contraindications: [],
          tags: [],
        },
        phases: [
          {
            index: 0 as never,
            phase: 'inhaling',
            duration: 1000 as never,
            curve: 'linear',
          },
        ],
        cycles: 1,
        totalDuration: 2000 as never,
        totalCycleDuration: 2000 as never,
        compiledAt: '2026-06-25T00:00:00.000Z' as never,
        compiledBy: 'compiler-1' as never,
        checksum: 'fnv1a:0000000000000000',
      });

      expect(Object.isFrozen(plan)).toBe(true);
      expect(Object.isFrozen(plan.metadata)).toBe(true);
      expect(Object.isFrozen(plan.phases)).toBe(true);
      expect(plan.title).toBe('Test');
    });

    it('preserves optional metadata fields', () => {
      const plan = buildExecutionPlan({
        executionId: ExecutionId('exec-1'),
        protocolId: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
        version: '1.0.0' as never,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
        compilerVersion: '1.0.0',
        title: 'T',
        metadata: {
          author: 'Author',
          language: 'en',
          references: ['ref1'],
          evidenceLevel: 'A',
          contraindications: [],
          category: 'calm',
          tags: ['focus'],
        },
        phases: [
          { index: 0 as never, phase: 'inhaling', duration: 1000 as never, curve: 'linear' },
        ],
        cycles: 1,
        totalDuration: 1000 as never,
        totalCycleDuration: 1000 as never,
        compiledAt: '2026-06-25T00:00:00.000Z' as never,
        compiledBy: 'compiler-1' as never,
        checksum: 'fnv1a:0000000000000000',
      });
      expect(plan.metadata.author).toBe('Author');
      expect(plan.metadata.references).toEqual(['ref1']);
      expect(plan.metadata.tags).toEqual(['focus']);
    });
  });
});