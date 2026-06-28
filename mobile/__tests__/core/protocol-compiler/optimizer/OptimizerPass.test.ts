/**
 * Optimizer pass tests.
 */

import { buildIR } from '../../../../src/core/protocol-compiler/ir/IRBuilder';
import {
  checksumPass,
  computeChecksum,
  computeExecutionId,
  normalizePhasesPass,
  precalculateCyclesPass,
  precalculateDurationsPass,
  removeRedundancyPass,
  runOptimizerPipeline,
} from '../../../../src/core/protocol-compiler/optimizer/OptimizerPass';
import {
  fourSevenEightProtocol,
  fullMetadataProtocol,
  minimalValidProtocol,
} from '../fixtures';
import { ProtocolId } from '@araflow/shared-contracts';

const NOW = (): number => 1_700_000_000_000;

describe('OptimizerPasses', () => {
  describe('normalizePhasesPass', () => {
    it('re-stamps indices', () => {
      const ir = buildIR(fullMetadataProtocol(), NOW);
      const normalized = normalizePhasesPass.apply(ir);
      for (let i = 0; i < normalized.breath.phases.length; i += 1) {
        expect(normalized.breath.phases[i]!.index).toBe(i);
      }
    });

    it('produces a new IR (does not mutate)', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const result = normalizePhasesPass.apply(ir);
      expect(result).not.toBe(ir);
    });
  });

  describe('removeRedundancyPass', () => {
    it('returns IR unchanged when there are no redundancies', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const result = removeRedundancyPass.apply(ir);
      expect(result.breath.phases.length).toBe(ir.breath.phases.length);
    });

    it('merges adjacent same-curve phases', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number; curve?: string }> }).phases = [
        { type: 'inhale', durationMs: 1000, curve: 'linear' },
        { type: 'inhale', durationMs: 2000, curve: 'linear' },
        { type: 'exhale', durationMs: 1000 },
      ];
      const ir = buildIR(doc, NOW);
      const result = removeRedundancyPass.apply(ir);
      expect(result.breath.phases.length).toBe(2);
    });

    it('returns IR unchanged for single-phase cycles', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
        { type: 'inhale', durationMs: 1000 },
      ];
      const ir = buildIR(doc, NOW);
      const result = removeRedundancyPass.apply(ir);
      expect(result.breath.phases.length).toBe(1);
    });

    it('does not merge phases with different curves', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number; curve?: string }> }).phases = [
        { type: 'inhale', durationMs: 1000, curve: 'ease-in' },
        { type: 'inhale', durationMs: 1000, curve: 'ease-out' },
        { type: 'exhale', durationMs: 1000 },
      ];
      const ir = buildIR(doc, NOW);
      const result = removeRedundancyPass.apply(ir);
      expect(result.breath.phases.length).toBe(3);
    });
  });

  describe('precalculateCyclesPass', () => {
    it('recomputes totalCycleMs', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const result = precalculateCyclesPass.apply(ir);
      expect(result.breath.totalCycleMs).toBe(19000);
    });

    it('recomputes ratios', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const result = precalculateCyclesPass.apply(ir);
      expect(result.breath.phases[0]!.ratio).toBeCloseTo(4000 / 19000, 5);
    });
  });

  describe('precalculateDurationsPass', () => {
    it('recomputes totalSessionMs', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const result = precalculateDurationsPass.apply(ir);
      expect(result.breath.totalSessionMs).toBe(19000 * 4 + 1000 * 3);
    });
  });

  describe('checksumPass', () => {
    it('returns IR unchanged', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const result = checksumPass.apply(ir);
      expect(result).toBe(ir);
    });

    it('extractChecksum returns same as computeChecksum', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const a = computeChecksum(ir);
      const b = checksumPass.extractChecksum(ir);
      expect(a).toBe(b);
    });

    it('is deterministic across runs', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const a = computeChecksum(ir);
      const b = computeChecksum(ir);
      expect(a).toBe(b);
    });

    it('changes when content changes', () => {
      const ir1 = buildIR(minimalValidProtocol(), NOW);
      const ir2 = buildIR(fourSevenEightProtocol(), NOW);
      expect(computeChecksum(ir1)).not.toBe(computeChecksum(ir2));
    });

    it('produces fnv1a: prefix', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      expect(computeChecksum(ir)).toMatch(/^fnv1a:/);
    });
  });

  describe('computeExecutionId', () => {
    it('produces exec- prefix', () => {
      expect(computeExecutionId('fnv1a:abc')).toMatch(/^exec-/);
    });

    it('is deterministic', () => {
      expect(computeExecutionId('fnv1a:abc')).toBe(computeExecutionId('fnv1a:abc'));
    });
  });

  describe('runOptimizerPipeline', () => {
    it('runs all passes in order', () => {
      const ir = buildIR(fourSevenEightProtocol(), NOW);
      const passes = [
        normalizePhasesPass,
        precalculateCyclesPass,
        precalculateDurationsPass,
      ];
      const result = runOptimizerPipeline(ir, passes);
      expect(result.passNames).toEqual(['normalize-phases', 'precalculate-cycles', 'precalculate-durations']);
    });

    it('returns a frozen pass list', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const result = runOptimizerPipeline(ir, [normalizePhasesPass]);
      expect(Object.isFrozen(result.passNames)).toBe(true);
    });

    it('handles empty passes', () => {
      const ir = buildIR(minimalValidProtocol(), NOW);
      const result = runOptimizerPipeline(ir, []);
      expect(result.passNames).toEqual([]);
    });
  });

  describe('Edge cases', () => {
    it('handles empty phases array in optimizer', () => {
      const ir = buildIR(
        {
          ...minimalValidProtocol(),
          id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
          breath: { cycles: 1, phases: [] },
        },
        NOW,
      );
      const result = precalculateCyclesPass.apply(ir);
      expect(result.breath.totalCycleMs).toBe(0);
    });
  });
});