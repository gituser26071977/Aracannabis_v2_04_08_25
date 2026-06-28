/**
 * Validators — schema, semantic, and version-compatibility checks.
 *
 * All validators take a ProtocolDocument and return an array of
 * Failure objects. Empty array = success. Failures are accumulated,
 * not short-circuited — the compiler reports all problems at once.
 *
 * Errors are typed via shared-contracts `Failure` shape so the
 * compiler can aggregate them into CompilerResult without conversion.
 */

import type { ProtocolDocument } from '../domain/ProtocolDocument';
import type { Failure } from '@araflow/shared-contracts';
import { Failure as makeFailure } from '@araflow/shared-contracts';

/**
 * SchemaValidator — structural rules not covered by parser.
 *
 * The parser checks shape and types. SchemaValidator checks limits,
 * enums, and structural invariants specific to the protocol domain.
 */
export class SchemaValidator {
  /** Max number of cycles in one protocol session. */
  public static readonly MAX_CYCLES = 100;
  /** Max number of phases in one cycle. */
  public static readonly MAX_PHASES = 16;
  /** Min phase duration in ms. */
  public static readonly MIN_PHASE_MS = 100;
  /** Max phase duration in ms (60s). */
  public static readonly MAX_PHASE_MS = 60_000;
  /** Min total session duration in ms (1s). */
  public static readonly MIN_SESSION_MS = 1_000;
  /** Max total session duration in ms (60min). */
  public static readonly MAX_SESSION_MS = 60 * 60 * 1_000;
  /** Max title length. */
  public static readonly MAX_TITLE_LENGTH = 100;
  /** Max description length. */
  public static readonly MAX_DESCRIPTION_LENGTH = 1_000;

  public validate(doc: ProtocolDocument): readonly Failure[] {
    const failures: Failure[] = [];

    // Title
    if (doc.title.length === 0) {
      failures.push(
        makeFailure({
          code: 'schema_title_empty',
          message: 'Title must not be empty',
          severity: 'error',
          path: '$.title',
        }),
      );
    }
    if (doc.title.length > SchemaValidator.MAX_TITLE_LENGTH) {
      failures.push(
        makeFailure({
          code: 'schema_title_too_long',
          message: `Title exceeds max length ${SchemaValidator.MAX_TITLE_LENGTH}`,
          severity: 'error',
          path: '$.title',
          context: { length: doc.title.length, max: SchemaValidator.MAX_TITLE_LENGTH },
        }),
      );
    }

    if (doc.description !== undefined && doc.description.length > SchemaValidator.MAX_DESCRIPTION_LENGTH) {
      failures.push(
        makeFailure({
          code: 'schema_description_too_long',
          message: `Description exceeds max length ${SchemaValidator.MAX_DESCRIPTION_LENGTH}`,
          severity: 'error',
          path: '$.description',
          context: { length: doc.description.length, max: SchemaValidator.MAX_DESCRIPTION_LENGTH },
        }),
      );
    }

    // Breath: cycles
    if (doc.breath.cycles < 1) {
      failures.push(
        makeFailure({
          code: 'schema_cycles_min',
          message: 'breath.cycles must be at least 1',
          severity: 'error',
          path: '$.breath.cycles',
          context: { received: doc.breath.cycles },
        }),
      );
    }
    if (doc.breath.cycles > SchemaValidator.MAX_CYCLES) {
      failures.push(
        makeFailure({
          code: 'schema_cycles_max',
          message: `breath.cycles must be at most ${SchemaValidator.MAX_CYCLES}`,
          severity: 'error',
          path: '$.breath.cycles',
          context: { received: doc.breath.cycles, max: SchemaValidator.MAX_CYCLES },
        }),
      );
    }

    // Breath: phases
    if (doc.breath.phases.length === 0) {
      failures.push(
        makeFailure({
          code: 'schema_phases_empty',
          message: 'breath.phases must contain at least one phase',
          severity: 'error',
          path: '$.breath.phases',
        }),
      );
    }
    if (doc.breath.phases.length > SchemaValidator.MAX_PHASES) {
      failures.push(
        makeFailure({
          code: 'schema_phases_too_many',
          message: `breath.phases exceeds max count ${SchemaValidator.MAX_PHASES}`,
          severity: 'error',
          path: '$.breath.phases',
          context: { count: doc.breath.phases.length, max: SchemaValidator.MAX_PHASES },
        }),
      );
    }

    // Each phase: duration
    doc.breath.phases.forEach((p, i) => {
      if (p.durationMs < SchemaValidator.MIN_PHASE_MS) {
        failures.push(
          makeFailure({
            code: 'schema_phase_duration_min',
            message: `Phase ${i} duration below minimum ${SchemaValidator.MIN_PHASE_MS}ms`,
            severity: 'error',
            path: `$.breath.phases[${i}].durationMs`,
            context: { received: p.durationMs, min: SchemaValidator.MIN_PHASE_MS },
          }),
        );
      }
      if (p.durationMs > SchemaValidator.MAX_PHASE_MS) {
        failures.push(
          makeFailure({
            code: 'schema_phase_duration_max',
            message: `Phase ${i} duration exceeds maximum ${SchemaValidator.MAX_PHASE_MS}ms`,
            severity: 'error',
            path: `$.breath.phases[${i}].durationMs`,
            context: { received: p.durationMs, max: SchemaValidator.MAX_PHASE_MS },
          }),
        );
      }
    });

    // Rest between cycles
    const rest = doc.breath.restBetweenCyclesMs ?? 0;
    if (rest < 0) {
      failures.push(
        makeFailure({
          code: 'schema_rest_negative',
          message: 'breath.restBetweenCyclesMs must be non-negative',
          severity: 'error',
          path: '$.breath.restBetweenCyclesMs',
          context: { received: rest },
        }),
      );
    }

    // Total session duration bounds
    const totalMs = computeTotalMs(doc);
    if (totalMs < SchemaValidator.MIN_SESSION_MS) {
      failures.push(
        makeFailure({
          code: 'schema_session_too_short',
          message: `Total session duration ${totalMs}ms below minimum ${SchemaValidator.MIN_SESSION_MS}ms`,
          severity: 'error',
          path: '$.breath',
          context: { totalMs, min: SchemaValidator.MIN_SESSION_MS },
        }),
      );
    }
    if (totalMs > SchemaValidator.MAX_SESSION_MS) {
      failures.push(
        makeFailure({
          code: 'schema_session_too_long',
          message: `Total session duration ${totalMs}ms exceeds maximum ${SchemaValidator.MAX_SESSION_MS}ms`,
          severity: 'error',
          path: '$.breath',
          context: { totalMs, max: SchemaValidator.MAX_SESSION_MS },
        }),
      );
    }

    return failures;
  }
}

/**
 * SemanticValidator — domain rules beyond pure schema.
 *
 * Rules:
 *   - Cycle must have at least one inhale and one exhale (humans must
 *     breathe both directions; pure hold-only cycles are nonsensical).
 *   - First phase should be inhale (warn if not).
 *   - Cycle must alternate inhale/exhale (warn on two consecutive
 *     inhales or exhales without a hold).
 *   - References must be valid URLs (warn).
 *   - Author required for published protocols (error if missing and
 *     category is set).
 *   - Approved protocols must have evidenceLevel (error if missing).
 *   - Category must be from a small whitelist (warn).
 */
export class SemanticValidator {
  public static readonly ALLOWED_CATEGORIES = [
    'wellness',
    'sleep',
    'focus',
    'recovery',
    'calm',
    'energy',
    'clinical',
  ] as const;

  public validate(doc: ProtocolDocument): readonly Failure[] {
    const failures: Failure[] = [];

    // Cycle must have at least one inhale and one exhale
    const hasInhale = doc.breath.phases.some(
      (p) => p.type === 'inhale' || p.type === 'hold-in',
    );
    const hasExhale = doc.breath.phases.some(
      (p) => p.type === 'exhale' || p.type === 'hold-out',
    );
    if (!hasInhale) {
      failures.push(
        makeFailure({
          code: 'semantic_no_inhale',
          message: 'Cycle must contain at least one inhale (or hold-in) phase',
          severity: 'error',
          path: '$.breath.phases',
        }),
      );
    }
    if (!hasExhale) {
      failures.push(
        makeFailure({
          code: 'semantic_no_exhale',
          message: 'Cycle must contain at least one exhale (or hold-out) phase',
          severity: 'error',
          path: '$.breath.phases',
        }),
      );
    }

    // First phase should be inhale (warning only)
    const first = doc.breath.phases[0];
    if (first !== undefined && first.type !== 'inhale') {
      failures.push(
        makeFailure({
          code: 'semantic_first_phase_not_inhale',
          message: `First phase is "${first.type}" — recommended is "inhale"`,
          severity: 'warn',
          path: '$.breath.phases[0]',
          context: { recommended: 'inhale', actual: first.type },
        }),
      );
    }

    // Consecutive same-direction phases
    for (let i = 1; i < doc.breath.phases.length; i += 1) {
      const prev = doc.breath.phases[i - 1]!;
      const curr = doc.breath.phases[i]!;
      if (
        (prev.type === 'inhale' || prev.type === 'hold-in') &&
        (curr.type === 'inhale' || curr.type === 'hold-in')
      ) {
        failures.push(
          makeFailure({
            code: 'semantic_consecutive_inhale',
            message: `Two consecutive inhale-class phases at index ${i - 1} and ${i}`,
            severity: 'warn',
            path: `$.breath.phases[${i}]`,
          }),
        );
      }
      if (
        (prev.type === 'exhale' || prev.type === 'hold-out') &&
        (curr.type === 'exhale' || curr.type === 'hold-out')
      ) {
        failures.push(
          makeFailure({
            code: 'semantic_consecutive_exhale',
            message: `Two consecutive exhale-class phases at index ${i - 1} and ${i}`,
            severity: 'warn',
            path: `$.breath.phases[${i}]`,
          }),
        );
      }
    }

    // Metadata semantic rules
    const md = doc.metadata;
    if (md?.category !== undefined && !this.isKnownCategory(md.category)) {
      failures.push(
        makeFailure({
          code: 'semantic_unknown_category',
          message: `Category "${md.category}" is not in the known set`,
          severity: 'warn',
          path: '$.metadata.category',
          context: { received: md.category, known: SemanticValidator.ALLOWED_CATEGORIES },
        }),
      );
    }

    if (md?.references !== undefined) {
      md.references.forEach((ref, i) => {
        if (!this.isPlausibleUrl(ref)) {
          failures.push(
            makeFailure({
              code: 'semantic_reference_malformed',
              message: `Reference ${i} is not a plausible URL or DOI`,
              severity: 'warn',
              path: `$.metadata.references[${i}]`,
              context: { value: ref },
            }),
          );
        }
      });
    }

    if (md?.category !== undefined && md.author === undefined) {
      failures.push(
        makeFailure({
          code: 'semantic_author_missing',
          message: 'Author is required when category is set',
          severity: 'error',
          path: '$.metadata.author',
        }),
      );
    }

    if (md?.approvedAt !== undefined && md.evidenceLevel === undefined) {
      failures.push(
        makeFailure({
          code: 'semantic_evidence_missing',
          message: 'evidenceLevel is required when approvedAt is set',
          severity: 'error',
          path: '$.metadata.evidenceLevel',
        }),
      );
    }

    return failures;
  }

  private isKnownCategory(c: string): boolean {
    return (SemanticValidator.ALLOWED_CATEGORIES as readonly string[]).includes(c);
  }

  private isPlausibleUrl(s: string): boolean {
    return (
      /^https?:\/\/.+/i.test(s) ||
      /^doi:10\.\d{4,9}\/[-._;()/:a-z0-9]+$/i.test(s)
    );
  }
}

/**
 * VersionCompatibilityValidator — checks protocol version compatibility.
 *
 * Rules:
 *   - Major version 0 is treated as experimental and emits a warning.
 *   - Future majors (compared to compiler's CURRENT_SCHEMA_MAJOR)
 *     produce an error.
 *   - Prerelease versions emit a warning.
 */
export class VersionCompatibilityValidator {
  public constructor(private readonly currentMajor: number) {}

  public validate(doc: ProtocolDocument): readonly Failure[] {
    const failures: Failure[] = [];
    const semver = doc.version as string;
    const majorMatch = /^(\d+)\./.exec(semver);
    const major = majorMatch !== null ? Number(majorMatch[1]) : NaN;

    if (!Number.isInteger(major)) {
      failures.push(
        makeFailure({
          code: 'compat_invalid_version',
          message: `Cannot parse major version from "${semver}"`,
          severity: 'error',
          path: '$.version',
          context: { version: semver },
        }),
      );
      return failures;
    }

    if (major === 0) {
      failures.push(
        makeFailure({
          code: 'compat_experimental_version',
          message: 'Version 0.x.x is experimental',
          severity: 'warn',
          path: '$.version',
          context: { version: semver },
        }),
      );
    }

    if (major > this.currentMajor) {
      failures.push(
        makeFailure({
          code: 'compat_future_major',
          message: `Protocol major version ${major} is newer than compiler's supported ${this.currentMajor}`,
          severity: 'error',
          path: '$.version',
          context: { received: major, supported: this.currentMajor },
        }),
      );
    }

    if (semver.includes('-')) {
      failures.push(
        makeFailure({
          code: 'compat_prerelease',
          message: `Prerelease version "${semver}" may not be stable`,
          severity: 'warn',
          path: '$.version',
          context: { version: semver },
        }),
      );
    }

    return failures;
  }
}

// REDACTED
// Private helpers
// REDACTED

const computeTotalMs = (doc: ProtocolDocument): number => {
  let cycleMs = 0;
  for (const p of doc.breath.phases) {
    cycleMs += p.durationMs;
  }
  const restMs = doc.breath.restBetweenCyclesMs ?? 0;
  return cycleMs * doc.breath.cycles + restMs * Math.max(0, doc.breath.cycles - 1);
};
