/**
 * Validators — schema, semantic, and version compatibility.
 */

import {
  SchemaValidator,
  SemanticValidator,
  VersionCompatibilityValidator,
} from '../../../../src/core/protocol-compiler/validation/Validators';
import {
  emptyPhasesProtocol,
  fourSevenEightProtocol,
  minimalValidProtocol,
  tooManyCyclesProtocol,
  tooShortPhaseProtocol,
} from '../fixtures';

describe('SchemaValidator', () => {
  const validator = new SchemaValidator();

  it('passes the minimal valid protocol', () => {
    const failures = validator.validate(minimalValidProtocol());
    expect(failures).toEqual([]);
  });

  it('passes the 4-7-8 protocol', () => {
    const failures = validator.validate(fourSevenEightProtocol());
    expect(failures).toEqual([]);
  });

  it('rejects empty title', () => {
    const doc = minimalValidProtocol();
    (doc as { title: string }).title = '';
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_title_empty')).toBe(true);
  });

  it('rejects title that exceeds max length', () => {
    const doc = minimalValidProtocol();
    (doc as { title: string }).title = 'a'.repeat(SchemaValidator.MAX_TITLE_LENGTH + 1);
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_title_too_long')).toBe(true);
  });

  it('rejects description that exceeds max length', () => {
    const doc = minimalValidProtocol();
    (doc as { description?: string }).description = 'a'.repeat(
      SchemaValidator.MAX_DESCRIPTION_LENGTH + 1,
    );
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_description_too_long')).toBe(true);
  });

  it('rejects cycles < 1', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { cycles: number }).cycles = 0;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_cycles_min')).toBe(true);
  });

  it('rejects cycles > MAX_CYCLES', () => {
    const failures = validator.validate(tooManyCyclesProtocol());
    expect(failures.some((f) => f.code === 'schema_cycles_max')).toBe(true);
  });

  it('rejects empty phases', () => {
    const failures = validator.validate(emptyPhasesProtocol());
    expect(failures.some((f) => f.code === 'schema_phases_empty')).toBe(true);
  });

  it('rejects too many phases', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: unknown[] }).phases = Array.from({ length: SchemaValidator.MAX_PHASES + 1 }, () => ({
      type: 'inhale' as const,
      durationMs: 1000,
    }));
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_phases_too_many')).toBe(true);
  });

  it('rejects phase duration below MIN_PHASE_MS', () => {
    const failures = validator.validate(tooShortPhaseProtocol());
    expect(failures.some((f) => f.code === 'schema_phase_duration_min')).toBe(true);
  });

  it('rejects phase duration above MAX_PHASE_MS', () => {
    const doc = minimalValidProtocol();
    (doc.breath.phases as Array<{ durationMs: number; type: string }>)[0]!.durationMs =
      SchemaValidator.MAX_PHASE_MS + 1;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_phase_duration_max')).toBe(true);
  });

  it('rejects negative restBetweenCyclesMs', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { restBetweenCyclesMs?: number }).restBetweenCyclesMs = -1;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_rest_negative')).toBe(true);
  });

  it('rejects session below MIN_SESSION_MS', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { cycles: number; phases: Array<{ durationMs: number; type: string }> }).phases = [
      { type: 'inhale', durationMs: 100 },
      { type: 'exhale', durationMs: 100 },
    ];
    (doc.breath as unknown as { cycles: number }).cycles = 1;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_session_too_short')).toBe(true);
  });

  it('rejects session above MAX_SESSION_MS', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { cycles: number; phases: Array<{ durationMs: number; type: string }> }).phases = [
      { type: 'inhale', durationMs: 60000 },
      { type: 'exhale', durationMs: 60000 },
    ];
    (doc.breath as unknown as { cycles: number }).cycles = SchemaValidator.MAX_CYCLES;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'schema_session_too_long')).toBe(true);
  });
});

describe('SemanticValidator', () => {
  const validator = new SemanticValidator();

  it('passes the 4-7-8 protocol (with no blocking errors)', () => {
    const failures = validator.validate(fourSevenEightProtocol());
    // 4-7-8 has inhale→hold-in which is a "consecutive inhale-class" warning,
    // not a blocking error. Filter by severity:
    const errors = failures.filter((f) => f.severity === 'error' || f.severity === 'fatal');
    expect(errors).toEqual([]);
  });

  it('errors when no inhale phase present', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
      { type: 'exhale', durationMs: 1000 },
    ];
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_no_inhale')).toBe(true);
  });

  it('errors when no exhale phase present', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
      { type: 'inhale', durationMs: 1000 },
    ];
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_no_exhale')).toBe(true);
  });

  it('warns when first phase is not inhale', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
      { type: 'exhale', durationMs: 1000 },
      { type: 'inhale', durationMs: 1000 },
    ];
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_first_phase_not_inhale')).toBe(true);
  });

  it('warns on consecutive inhale-class phases', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
      { type: 'inhale', durationMs: 1000 },
      { type: 'hold-in', durationMs: 1000 },
      { type: 'exhale', durationMs: 1000 },
    ];
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_consecutive_inhale')).toBe(true);
  });

  it('warns on consecutive exhale-class phases', () => {
    const doc = minimalValidProtocol();
    (doc.breath as unknown as { phases: Array<{ type: string; durationMs: number }> }).phases = [
      { type: 'inhale', durationMs: 1000 },
      { type: 'exhale', durationMs: 1000 },
      { type: 'hold-out', durationMs: 1000 },
    ];
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_consecutive_exhale')).toBe(true);
  });

  it('warns on unknown category', () => {
    const doc = fourSevenEightProtocol();
    if (doc.metadata) {
      (doc.metadata as { category?: string }).category = 'mystery';
    }
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_unknown_category')).toBe(true);
  });

  it('warns on malformed reference URL', () => {
    const doc = fourSevenEightProtocol();
    if (doc.metadata) {
      (doc.metadata as { references?: string[] }).references = ['not-a-url'];
    }
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_reference_malformed')).toBe(true);
  });

  it('accepts DOI-formatted references', () => {
    const doc = fourSevenEightProtocol();
    if (doc.metadata) {
      (doc.metadata as { references?: string[] }).references = ['doi:10.1000/xyz123'];
    }
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_reference_malformed')).toBe(false);
  });

  it('errors when category set but author missing', () => {
    const doc = fourSevenEightProtocol();
    if (doc.metadata) {
      delete (doc.metadata as { author?: string }).author;
    }
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_author_missing')).toBe(true);
  });

  it('errors when approvedAt set but evidenceLevel missing', () => {
    const doc = fourSevenEightProtocol();
    if (doc.metadata) {
      delete (doc.metadata as { evidenceLevel?: string }).evidenceLevel;
    }
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'semantic_evidence_missing')).toBe(true);
  });
});

describe('VersionCompatibilityValidator', () => {
  it('returns no failures for a normal version', () => {
    const validator = new VersionCompatibilityValidator(1);
    const failures = validator.validate(minimalValidProtocol());
    expect(failures).toEqual([]);
  });

  it('warns for major 0 (experimental)', () => {
    const validator = new VersionCompatibilityValidator(1);
    const doc = minimalValidProtocol();
    (doc as { version: string }).version = '0.1.0' as never;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'compat_experimental_version')).toBe(true);
  });

  it('errors when protocol major is newer than compiler', () => {
    const validator = new VersionCompatibilityValidator(1);
    const doc = minimalValidProtocol();
    (doc as { version: string }).version = '2.0.0' as never;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'compat_future_major')).toBe(true);
  });

  it('warns for prerelease versions', () => {
    const validator = new VersionCompatibilityValidator(1);
    const doc = minimalValidProtocol();
    (doc as { version: string }).version = '1.0.0-rc.1' as never;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'compat_prerelease')).toBe(true);
  });

  it('errors when version is unparseable', () => {
    const validator = new VersionCompatibilityValidator(1);
    const doc = minimalValidProtocol();
    (doc as { version: string }).version = 'abc' as never;
    const failures = validator.validate(doc);
    expect(failures.some((f) => f.code === 'compat_invalid_version')).toBe(true);
  });
});