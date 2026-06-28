/**
 * ProtocolLinter tests.
 */

import {
  checksumInconsistencyRule,
  emptyProtocolRule,
  invalidDurationRule,
  missingDescriptionRule,
  missingMetadataRule,
  ProtocolLinter,
  redundantStepsRule,
  unusualCycleCountRule,
} from '../../../../src/core/protocol-compiler/linter/ProtocolLinter';
import {
  fourSevenEightProtocol,
  minimalValidProtocol,
} from '../fixtures';
import { buildIR } from '../../../../src/core/protocol-compiler/ir/IRBuilder';
import { checksumPass } from '../../../../src/core/protocol-compiler/optimizer/OptimizerPass';

const NOW = (): number => 1_700_000_000_000;

describe('ProtocolLinter', () => {
  describe('redundantStepsRule', () => {
    it('warns when a phase type appears more than 2 times', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
        { type: 'inhale', durationMs: 1000 },
        { type: 'hold-in', durationMs: 1000 },
        { type: 'hold-in', durationMs: 1000 },
        { type: 'hold-in', durationMs: 1000 },
        { type: 'exhale', durationMs: 1000 },
      ];
      const findings = redundantStepsRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_redundant_phase_type')).toBe(true);
    });

    it('does not warn on 2 or fewer', () => {
      const findings = redundantStepsRule.apply(minimalValidProtocol(), null, null);
      expect(findings).toEqual([]);
    });
  });

  describe('invalidDurationRule', () => {
    it('warns on duration not multiple of 100ms', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases[0]!.durationMs = 1234;
      const findings = invalidDurationRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'REDACTED')).toBe(true);
    });

    it('passes when all durations are multiples of 100ms', () => {
      const findings = invalidDurationRule.apply(fourSevenEightProtocol(), null, null);
      expect(findings).toEqual([]);
    });
  });

  describe('missingMetadataRule', () => {
    it('warns when metadata is completely missing', () => {
      const findings = missingMetadataRule.apply(minimalValidProtocol(), null, null);
      expect(findings.some((f) => f.code === 'lint_metadata_completely_missing')).toBe(true);
    });

    it('warns on missing author', () => {
      const doc = fourSevenEightProtocol();
      if (doc.metadata) delete (doc.metadata as { author?: string }).author;
      const findings = missingMetadataRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_metadata_author_missing')).toBe(true);
    });

    it('warns on missing references', () => {
      const doc = fourSevenEightProtocol();
      if (doc.metadata) (doc.metadata as { references?: string[] }).references = [];
      const findings = missingMetadataRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_metadata_references_empty')).toBe(true);
    });

    it('warns on missing evidenceLevel', () => {
      const doc = fourSevenEightProtocol();
      if (doc.metadata) delete (doc.metadata as { evidenceLevel?: string }).evidenceLevel;
      const findings = missingMetadataRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_metadata_evidence_missing')).toBe(true);
    });
  });

  describe('emptyProtocolRule', () => {
    it('warns on empty phases', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { phases: unknown[] }).phases = [];
      const findings = emptyProtocolRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_empty_protocol')).toBe(true);
    });

    it('warns on zero cycles', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { cycles: number }).cycles = 0;
      const findings = emptyProtocolRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_zero_cycles')).toBe(true);
    });
  });

  describe('checksumInconsistencyRule', () => {
    it('warns when declared checksum mismatches', () => {
      const doc = fourSevenEightProtocol();
      (doc as { checksum?: string }).checksum = 'mismatch';
      const ir = buildIR(doc, NOW);
      const findings = checksumInconsistencyRule.apply(doc, ir, null);
      expect(findings.some((f) => f.code === 'lint_checksum_mismatch')).toBe(true);
    });

    it('passes when IR is null', () => {
      const doc = fourSevenEightProtocol();
      const findings = checksumInconsistencyRule.apply(doc, null, null);
      expect(findings).toEqual([]);
    });

    it('passes when no declared checksum', () => {
      const doc = fourSevenEightProtocol();
      const ir = buildIR(doc, NOW);
      const findings = checksumInconsistencyRule.apply(doc, ir, null);
      expect(findings).toEqual([]);
    });
  });

  describe('unusualCycleCountRule', () => {
    it('warns when cycles > 50', () => {
      const doc = minimalValidProtocol();
      (doc.breath as unknown as { cycles: number }).cycles = 51;
      const findings = unusualCycleCountRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_high_cycle_count')).toBe(true);
    });

    it('passes for <= 50 cycles', () => {
      const findings = unusualCycleCountRule.apply(fourSevenEightProtocol(), null, null);
      expect(findings).toEqual([]);
    });
  });

  describe('missingDescriptionRule', () => {
    it('warns when no description', () => {
      const findings = missingDescriptionRule.apply(minimalValidProtocol(), null, null);
      expect(findings.some((f) => f.code === 'lint_description_missing')).toBe(true);
    });

    it('passes when description is present', () => {
      const findings = missingDescriptionRule.apply(fourSevenEightProtocol(), null, null);
      expect(findings).toEqual([]);
    });

    it('warns when description is empty string', () => {
      const doc = minimalValidProtocol();
      (doc as { description?: string }).description = '';
      const findings = missingDescriptionRule.apply(doc, null, null);
      expect(findings.some((f) => f.code === 'lint_description_missing')).toBe(true);
    });
  });

  describe('ProtocolLinter composite', () => {
    it('runs all rules and freezes findings', () => {
      const linter = new ProtocolLinter();
      const findings = linter.lint(minimalValidProtocol(), null, null);
      expect(Object.isFrozen(findings)).toBe(true);
    });

    it('accepts custom rules', () => {
      const linter = new ProtocolLinter([missingDescriptionRule]);
      const findings = linter.lint(minimalValidProtocol(), null, null);
      expect(findings.some((f) => f.code === 'lint_description_missing')).toBe(true);
      // other rules should NOT have been applied
      expect(findings.some((f) => f.code === 'lint_empty_protocol')).toBe(false);
    });

    it('uses checksum IR when available', () => {
      const doc = fourSevenEightProtocol();
      const ir = buildIR(doc, NOW);
      // Pass plan: irrelevant but used by lint signature
      void checksumPass;
      const linter = new ProtocolLinter([checksumInconsistencyRule]);
      const findings = linter.lint(doc, ir, null);
      expect(findings).toEqual([]);
    });
  });
});