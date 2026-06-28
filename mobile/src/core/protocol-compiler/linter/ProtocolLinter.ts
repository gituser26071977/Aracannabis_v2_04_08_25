/**
 * ProtocolLinter — generates non-blocking warnings for protocol documents.
 *
 * The linter does NOT prevent execution. Its findings are surfaced as
 * warnings to the user (developer at compile time; clinician in a UI
 * later). They are useful for catching quality issues early.
 *
 * Rules:
 *   - RedundantStepsRule: cycle has > 2 phases of the same type
 *   - InvalidDurationRule: phase duration not a multiple of 100ms
 *     (suggests unintentional timing)
 *   - MissingMetadataRule: missing author/references/evidenceLevel
 *   - EmptyProtocolRule: protocol has 0 cycles or 0 phases (already
 *     caught by SchemaValidator, but flagged here for clearer UX)
 *   - ChecksumInconsistencyRule: source declared checksum doesn't
 *     match computed
 *   - UnusualCycleCountRule: cycles > 50 (unusually long session)
 *   - MissingDescriptionRule: no description provided
 */

import type { ProtocolDocument } from '../domain/ProtocolDocument';
import type { ProtocolIR } from '../domain/IntermediateRepresentation';
import type { ProtocolExecutionPlan } from '../domain/ExecutionPlan';
import type { Failure } from '@araflow/shared-contracts';
import { Failure as makeFailure } from '@araflow/shared-contracts';
import { checksumPass } from '../optimizer/OptimizerPass';

/**
 * Single linter rule — pure function from inputs to warnings.
 */
export interface LintRule {
  readonly name: string;
  readonly apply: (
    doc: ProtocolDocument,
    ir: ProtocolIR | null,
    plan: ProtocolExecutionPlan | null,
  ) => readonly Failure[];
}

/**
 * ProtocolLinter — runs all registered rules and accumulates findings.
 *
 * Pure data structure; rules are stateless.
 */
export class ProtocolLinter {
  private readonly rules: LintRule[];

  public constructor(rules?: readonly LintRule[]) {
    this.rules = rules !== undefined ? [...rules] : defaultRules();
  }

  public lint(
    doc: ProtocolDocument,
    ir: ProtocolIR | null,
    plan: ProtocolExecutionPlan | null,
  ): readonly Failure[] {
    const findings: Failure[] = [];
    for (const rule of this.rules) {
      findings.push(...rule.apply(doc, ir, plan));
    }
    return Object.freeze(findings);
  }
}

// =============================================================================
// Rules
// =============================================================================

export const redundantStepsRule: LintRule = {
  name: 'redundant-steps',
  apply: (doc) => {
    const counts = countByType(doc);
    const findings: Failure[] = [];
    for (const [type, count] of counts) {
      if (count > 2) {
        findings.push(
          makeFailure({
            code: 'lint_redundant_phase_type',
            message: `Phase type "${type}" appears ${count} times in one cycle — consider simplifying`,
            severity: 'warn',
            path: '$.breath.phases',
            context: { type, count },
          }),
        );
      }
    }
    return findings;
  },
};

export const invalidDurationRule: LintRule = {
  name: 'invalid-duration',
  apply: (doc) => {
    const findings: Failure[] = [];
    doc.breath.phases.forEach((p, i) => {
      if (p.durationMs % 100 !== 0) {
        findings.push(
          makeFailure({
            code: 'REDACTED',
            message: `Phase ${i} duration ${p.durationMs}ms is not a multiple of 100ms`,
            severity: 'warn',
            path: `$.breath.phases[${i}].durationMs`,
            context: { received: p.durationMs },
          }),
        );
      }
    });
    return findings;
  },
};

export const missingMetadataRule: LintRule = {
  name: 'missing-metadata',
  apply: (doc) => {
    const findings: Failure[] = [];
    const md = doc.metadata;
    if (md === undefined) {
      findings.push(
        makeFailure({
          code: 'lint_metadata_completely_missing',
          message: 'Protocol has no metadata — author, references, and evidence cannot be verified',
          severity: 'warn',
          path: '$.metadata',
        }),
      );
      return findings;
    }
    if (md.author === undefined) {
      findings.push(
        makeFailure({
          code: 'lint_metadata_author_missing',
          message: 'Author is missing from metadata',
          severity: 'warn',
          path: '$.metadata.author',
        }),
      );
    }
    if (md.references === undefined || md.references.length === 0) {
      findings.push(
        makeFailure({
          code: 'lint_metadata_references_empty',
          message: 'No references provided — evidence base cannot be verified',
          severity: 'warn',
          path: '$.metadata.references',
        }),
      );
    }
    if (md.evidenceLevel === undefined) {
      findings.push(
        makeFailure({
          code: 'lint_metadata_evidence_missing',
          message: 'Evidence level not specified',
          severity: 'warn',
          path: '$.metadata.evidenceLevel',
        }),
      );
    }
    return findings;
  },
};

export const emptyProtocolRule: LintRule = {
  name: 'empty-protocol',
  apply: (doc) => {
    const findings: Failure[] = [];
    if (doc.breath.phases.length === 0) {
      findings.push(
        makeFailure({
          code: 'lint_empty_protocol',
          message: 'Protocol has no phases',
          severity: 'warn',
          path: '$.breath.phases',
        }),
      );
    }
    if (doc.breath.cycles === 0) {
      findings.push(
        makeFailure({
          code: 'lint_zero_cycles',
          message: 'Protocol has zero cycles',
          severity: 'warn',
          path: '$.breath.cycles',
        }),
      );
    }
    return findings;
  },
};

export const checksumInconsistencyRule: LintRule = {
  name: 'checksum-inconsistency',
  apply: (doc, ir) => {
    const findings: Failure[] = [];
    if (doc.checksum === undefined || ir === null) return findings;
    const computed = checksumPass.extractChecksum(ir);
    if (doc.checksum !== computed) {
      findings.push(
        makeFailure({
          code: 'lint_checksum_mismatch',
          message: 'Declared checksum does not match computed checksum',
          severity: 'warn',
          path: '$.checksum',
          context: { declared: doc.checksum, computed },
        }),
      );
    }
    return findings;
  },
};

export const unusualCycleCountRule: LintRule = {
  name: 'unusual-cycle-count',
  apply: (doc) => {
    const findings: Failure[] = [];
    if (doc.breath.cycles > 50) {
      findings.push(
        makeFailure({
          code: 'lint_high_cycle_count',
          message: `Protocol has ${doc.breath.cycles} cycles — unusually long session`,
          severity: 'warn',
          path: '$.breath.cycles',
          context: { cycles: doc.breath.cycles },
        }),
      );
    }
    return findings;
  },
};

export const missingDescriptionRule: LintRule = {
  name: 'missing-description',
  apply: (doc) => {
    if (doc.description === undefined || doc.description.length === 0) {
      return [
        makeFailure({
          code: 'lint_description_missing',
          message: 'No description provided',
          severity: 'warn',
          path: '$.description',
        }),
      ];
    }
    return [];
  },
};

// REDACTED
// Helpers
// REDACTED

const countByType = (doc: ProtocolDocument): Map<string, number> => {
  const m = new Map<string, number>();
  for (const p of doc.breath.phases) {
    m.set(p.type, (m.get(p.type) ?? 0) + 1);
  }
  return m;
};

const defaultRules = (): LintRule[] => [
  redundantStepsRule,
  invalidDurationRule,
  missingMetadataRule,
  emptyProtocolRule,
  checksumInconsistencyRule,
  unusualCycleCountRule,
  missingDescriptionRule,
];
