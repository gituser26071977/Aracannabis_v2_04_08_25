/**
 * JsonProtocolParser — parses JSON-encoded protocol sources.
 *
 * Pipeline:
 *   1. JSON.parse → raw object
 *   2. Structural validation against DocumentSchema (shape + types)
 *   3. Coercion: identity types (ProtocolId, SemanticVersion) via ctor
 *
 * Returns Result<ProtocolDocument, ValidationError>. Never throws for
 * expected input issues (malformed JSON, missing fields, wrong types).
 */

import {
  ProtocolId,
  SemanticVersion,
  Iso8601,
  Ok,
  Err,
  AppError,
  ValidationError,
  type Result,
} from '@araflow/shared-contracts';

import type { ProtocolParser, ParserCapabilities } from '../domain/ProtocolParser';
import type { ProtocolSource } from '../domain/ProtocolSource';
import type { ProtocolDocument, DocumentPhase, DocumentMetadata } from '../domain/ProtocolDocument';
import { DOCUMENT_PHASE_TYPES, isDocumentPhaseType } from '../domain/DocumentPhaseType';
import { DOCUMENT_CURVE_TYPES, isDocumentCurveType } from '../domain/DocumentCurve';
import { isEvidenceLevel } from '../domain/ProtocolDocument';
import { DEFAULT_SCHEMA_URI } from '../domain/SchemaVersion';

const PROTOCOL_PARSER_VERSION = '1.0.0' as const;

/**
 * JsonProtocolParser implementation.
 */
export class JsonProtocolParser implements ProtocolParser {
  public readonly capabilities: ParserCapabilities = Object.freeze({
    format: 'json' as const,
    version: PROTOCOL_PARSER_VERSION,
  });

  /**
   * Parses a JSON source into a ProtocolDocument.
   */
  public parse(source: ProtocolSource): Result<ProtocolDocument, ValidationError> {
    if (source.format !== 'json') {
      return Err(
        new ValidationError(
          `JsonProtocolParser cannot parse format: ${String(source.format)}`,
          {
            code: 'parser_format_mismatch',
            severity: 'error',
            context: { format: String(source.format) },
          },
        ),
      );
    }

    // Step 1: JSON.parse
    const parsed = safeJsonParse(source.raw);
    if (!parsed.ok) {
      return Err(
        new ValidationError(parsed.error.message, {
          code: 'json_parse_error',
          severity: 'error',
          path: '$',
          context: { detail: parsed.error.message },
        }),
      );
    }

    // Step 2: Structural validation
    const structural = this.validateStructure(parsed.value);
    if (!structural.ok) {
      return Err(structural.error);
    }

    // Step 3: Coerce to typed document
    return this.coerce(parsed.value, source.origin);
  }

  // REDACTED
  // Private helpers
  // REDACTED

  private validateStructure(raw: unknown): Result<true, ValidationError> {
    if (typeof raw !== 'object' || raw === null) {
      return Err(
        new ValidationError('Protocol document must be a JSON object', {
          code: 'document_not_object',
          severity: 'error',
          path: '$',
        }),
      );
    }
    const obj = raw as Record<string, unknown>;

    // Required top-level fields (note: $schema is optional, defaults to v1)
    const requiredTopLevel = ['id', 'version', 'title', 'breath'] as const;
    for (const field of requiredTopLevel) {
      if (!(field in obj)) {
        return Err(
          new ValidationError(`Missing required field: ${field}`, {
            code: 'document_missing_field',
            severity: 'error',
            path: `$.${field}`,
            context: { field },
          }),
        );
      }
    }

    // $schema: optional, but if present must be a string
    const schemaVal = obj['$schema'];
    if (schemaVal !== undefined && typeof schemaVal !== 'string') {
      return Err(
        new ValidationError('Field "$schema" must be a string', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.$schema',
        }),
      );
    }
    const idVal = obj['id'];
    if (typeof idVal !== 'string' || idVal.length === 0) {
      return Err(
        new ValidationError('Field "id" must be a non-empty string', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.id',
        }),
      );
    }
    const versionVal = obj['version'];
    if (typeof versionVal !== 'string' || versionVal.length === 0) {
      return Err(
        new ValidationError('Field "version" must be a non-empty string', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.version',
        }),
      );
    }
    const titleVal = obj['title'];
    if (typeof titleVal !== 'string' || titleVal.length === 0) {
      return Err(
        new ValidationError('Field "title" must be a non-empty string', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.title',
        }),
      );
    }

    // breath section
    const breathVal = obj['breath'];
    if (typeof breathVal !== 'object' || breathVal === null) {
      return Err(
        new ValidationError('Field "breath" must be an object', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.breath',
        }),
      );
    }
    const breath = breathVal as Record<string, unknown>;
    const cyclesVal = breath['cycles'];
    if (typeof cyclesVal !== 'number' || !Number.isInteger(cyclesVal)) {
      return Err(
        new ValidationError('Field "breath.cycles" must be an integer', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.breath.cycles',
        }),
      );
    }
    const phasesVal = breath['phases'];
    if (!Array.isArray(phasesVal)) {
      return Err(
        new ValidationError('Field "breath.phases" must be an array', {
          code: 'document_invalid_type',
          severity: 'error',
          path: '$.breath.phases',
        }),
      );
    }

    // Each phase
    const phasesArr = phasesVal as Array<unknown>;
    for (let i = 0; i < phasesArr.length; i += 1) {
      const phase = phasesArr[i];
      if (typeof phase !== 'object' || phase === null) {
        return Err(
          new ValidationError(`Phase ${i} must be an object`, {
            code: 'document_invalid_type',
            severity: 'error',
            path: `$.breath.phases[${i}]`,
          }),
        );
      }
      const p = phase as Record<string, unknown>;
      if (!isDocumentPhaseType(p['type'])) {
        return Err(
          new ValidationError(
            `Phase ${i}.type must be one of: ${DOCUMENT_PHASE_TYPES.join(', ')}`,
            {
              code: 'document_invalid_type',
              severity: 'error',
              path: `$.breath.phases[${i}].type`,
              context: { received: String(p['type']), allowed: DOCUMENT_PHASE_TYPES },
            },
          ),
        );
      }
      const durVal = p['durationMs'];
      if (typeof durVal !== 'number' || !Number.isInteger(durVal)) {
        return Err(
          new ValidationError(`Phase ${i}.durationMs must be an integer`, {
            code: 'document_invalid_type',
            severity: 'error',
            path: `$.breath.phases[${i}].durationMs`,
          }),
        );
      }
      const curveVal = p['curve'];
      if (curveVal !== undefined && !isDocumentCurveType(curveVal)) {
        return Err(
          new ValidationError(
            `Phase ${i}.curve must be one of: ${DOCUMENT_CURVE_TYPES.join(', ')}`,
            {
              code: 'document_invalid_type',
              severity: 'error',
              path: `$.breath.phases[${i}].curve`,
              context: { received: String(curveVal), allowed: DOCUMENT_CURVE_TYPES },
            },
          ),
        );
      }
    }

    // Optional metadata
    const metadataVal = obj['metadata'];
    if (metadataVal !== undefined) {
      if (typeof metadataVal !== 'object' || metadataVal === null) {
        return Err(
          new ValidationError('Field "metadata" must be an object', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata',
          }),
        );
      }
      const md = metadataVal as Record<string, unknown>;
      const evidenceVal = md['evidenceLevel'];
      if (evidenceVal !== undefined && !isEvidenceLevel(evidenceVal)) {
        return Err(
          new ValidationError('Field "metadata.evidenceLevel" must be A, B, C, or D', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata.evidenceLevel',
          }),
        );
      }
      const referencesVal = md['references'];
      if (referencesVal !== undefined && !Array.isArray(referencesVal)) {
        return Err(
          new ValidationError('Field "metadata.references" must be an array', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata.references',
          }),
        );
      }
      const contraVal = md['contraindications'];
      if (contraVal !== undefined && !Array.isArray(contraVal)) {
        return Err(
          new ValidationError('Field "metadata.contraindications" must be an array', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata.contraindications',
          }),
        );
      }
      const tagsVal = md['tags'];
      if (tagsVal !== undefined && !Array.isArray(tagsVal)) {
        return Err(
          new ValidationError('Field "metadata.tags" must be an array', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata.tags',
          }),
        );
      }
      const approvedVal = md['approvedAt'];
      if (approvedVal !== undefined && typeof approvedVal !== 'string') {
        return Err(
          new ValidationError('Field "metadata.approvedAt" must be a string', {
            code: 'document_invalid_type',
            severity: 'error',
            path: '$.metadata.approvedAt',
          }),
        );
      }
    }

    return Ok(true);
  }

  private coerce(raw: unknown, origin?: string): Result<ProtocolDocument, ValidationError> {
    const obj = raw as Record<string, unknown>;
    const breathRaw = obj['breath'] as Record<string, unknown>;

    // Identity: validate formats
    let protocolId: ProtocolId;
    try {
      protocolId = ProtocolId(String(obj['id']));
    } catch (e) {
      return Err(toValidationError(e, '$.id'));
    }

    let version: SemanticVersion;
    try {
      version = SemanticVersion(String(obj['version']));
    } catch (e) {
      return Err(toValidationError(e, '$.version'));
    }

    // Phases
    const phasesRaw = breathRaw['phases'] as Array<Record<string, unknown>>;
    const phases: DocumentPhase[] = [];
    for (let i = 0; i < phasesRaw.length; i += 1) {
      const p = phasesRaw[i]!;
      const phase: DocumentPhase =
        p['curve'] !== undefined
          ? {
              type: p['type'] as DocumentPhase['type'],
              durationMs: p['durationMs'] as number,
              curve: p['curve'] as NonNullable<DocumentPhase['curve']>,
            }
          : {
              type: p['type'] as DocumentPhase['type'],
              durationMs: p['durationMs'] as number,
            };
      phases.push(phase);
    }

    const breath: ProtocolDocument['breath'] = {
      cycles: breathRaw['cycles'] as number,
      phases,
      ...(breathRaw['restBetweenCyclesMs'] !== undefined
        ? { restBetweenCyclesMs: breathRaw['restBetweenCyclesMs'] as number }
        : {}),
    };

    // Metadata (all fields optional)
    let metadata: DocumentMetadata | undefined;
    const metadataObj = obj['metadata'];
    if (metadataObj !== undefined) {
      const md = metadataObj as Record<string, unknown>;
      const built: {
        author?: string;
        language?: string;
        references?: readonly string[];
        evidenceLevel?: 'A' | 'B' | 'C' | 'D';
        contraindications?: readonly string[];
        category?: string;
        tags?: readonly string[];
        approvedAt?: ReturnType<typeof Iso8601>;
      } = {};
      if (typeof md['author'] === 'string') built.author = md['author'];
      if (typeof md['language'] === 'string') built.language = md['language'];
      if (Array.isArray(md['references'])) built.references = md['references'] as string[];
      if (isEvidenceLevel(md['evidenceLevel'])) built.evidenceLevel = md['evidenceLevel'];
      if (Array.isArray(md['contraindications'])) built.contraindications = md['contraindications'] as string[];
      if (typeof md['category'] === 'string') built.category = md['category'];
      if (Array.isArray(md['tags'])) built.tags = md['tags'] as string[];
      const approvedAtVal = md['approvedAt'];
      if (typeof approvedAtVal === 'string') {
        try {
          built.approvedAt = Iso8601(approvedAtVal);
        } catch (e) {
          return Err(toValidationError(e, '$.metadata.approvedAt'));
        }
      }
      metadata = built;
    }

    const doc: ProtocolDocument = {
      $schema: typeof obj['$schema'] === 'string' ? obj['$schema'] : DEFAULT_SCHEMA_URI,
      id: protocolId,
      version,
      title: String(obj['title']),
      ...(typeof obj['subtitle'] === 'string' ? { subtitle: obj['subtitle'] } : {}),
      ...(typeof obj['description'] === 'string' ? { description: obj['description'] } : {}),
      breath,
      ...(metadata !== undefined ? { metadata } : {}),
      ...(typeof obj['checksum'] === 'string' ? { checksum: obj['checksum'] } : {}),
    };

    // origin is a parser-side concern; carry it via a side channel
    // that we discard here. The compiler records it elsewhere.
    void origin;
    return Ok(doc);
  }
}

const safeJsonParse = (
  raw: string,
): { readonly ok: true; readonly value: unknown } | { readonly ok: false; readonly error: Error } => {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e : new Error(String(e)) };
  }
};

const toValidationError = (e: unknown, path: string): ValidationError => {
  if (e instanceof AppError) {
    return new ValidationError(e.message, {
      code: e.code,
      severity: e.severity,
      path,
      context: e.context,
      cause: e.cause,
    });
  }
  return new ValidationError(String(e), {
    code: 'document_coercion_failed',
    severity: 'error',
    path,
    context: { error: String(e) },
  });
};