/**
 * ExecutionPlanBuilder tests.
 */

import { buildIR } from '../../../../src/core/protocol-compiler/ir/IRBuilder';
import { buildExecutionPlanFromIR } from '../../../../src/core/protocol-compiler/compiler/ExecutionPlanBuilder';
import { checksumPass } from '../../../../src/core/protocol-compiler/optimizer/OptimizerPass';
import {
  fourSevenEightProtocol,
  fullMetadataProtocol,
  minimalValidProtocol,
} from '../fixtures';
import { EngineId } from '@araflow/shared-contracts';

const NOW = (): number => 1_700_000_000_000;
const COMPILER_ID = EngineId('protocol-compiler');

describe('ExecutionPlanBuilder', () => {
  describe('buildExecutionPlanFromIR', () => {
    it('builds a plan from a minimal IR', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const optimized = checksumPass.apply(ir);
      const plan = buildExecutionPlanFromIR({
        ir: optimized,
        compiledBy: COMPILER_ID,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
      });
      expect(plan.protocolId).toBe(minimalValidProtocol().id);
      expect(plan.cycles).toBe(1);
      expect(plan.phases).toHaveLength(2);
      expect(plan.executionId).toMatch(/^exec-/);
      expect(plan.checksum).toMatch(/^fnv1a:/);
      expect(plan.compilerVersion).toContain('1.0.0');
    });

    it('preserves all phases', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const optimized = checksumPass.apply(ir);
      const plan = buildExecutionPlanFromIR({
        ir: optimized,
        compiledBy: COMPILER_ID,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
      });
      expect(plan.phases).toHaveLength(3);
      expect(plan.phases[0]!.phase).toBe('inhaling');
    });

    it('produces a frozen plan', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const optimized = checksumPass.apply(ir);
      const plan = buildExecutionPlanFromIR({
        ir: optimized,
        compiledBy: COMPILER_ID,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
      });
      expect(Object.isFrozen(plan)).toBe(true);
      expect(Object.isFrozen(plan.phases)).toBe(true);
      expect(Object.isFrozen(plan.metadata)).toBe(true);
    });

    it('preserves all metadata', () => {
      const ir = buildIR(fullMetadataProtocol(), NOW);
      const optimized = checksumPass.apply(ir);
      const plan = buildExecutionPlanFromIR({
        ir: optimized,
        compiledBy: COMPILER_ID,
        schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
      });
      expect(plan.metadata.author).toBe('Author Name');
      expect(plan.metadata.references).toHaveLength(2);
      expect(plan.metadata.tags).toEqual(['focus', 'energy']);
    });
  });
});