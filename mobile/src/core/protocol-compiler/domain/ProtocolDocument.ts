/**
 * ProtocolDocument — the typed result of parsing a protocol source.
 *
 * This is the source-of-truth intermediate shape between the parser
 * and the validators / IR builder. It contains:
 *   - Identity (id, version, schema)
 *   - Human-readable metadata (title, description, language)
 *   - Authorial / regulatory metadata (author, references,
 *     evidenceLevel, contraindications, category, tags)
 *   - Execution configuration (phases, cycles, durations)
 *   - Optional checksum for tamper detection
 *
 * All metadata is preserved INTACT. The compiler does not interpret
 * fields like author, language, references, evidenceLevel,
 * contraindications, or category — those pass through to the IR
 * unchanged.
 */

import type {
  ProtocolId,
  SemanticVersion,
  Duration,
  Iso8601,
} from '@araflow/shared-contracts';
import type { DocumentPhaseType } from './DocumentPhaseType';
import type { DocumentCurveType } from './DocumentCurve';

/**
 * ProtocolSourceFormat — accepted document encodings.
 */
export type ProtocolSourceFormat = 'json';

/**
 * EvidenceLevel — GRADE-like scientific evidence classification.
 *
 * Preserved as a string in the IR; the compiler does not interpret it.
 */
export type EvidenceLevel = 'A' | 'B' | 'C' | 'D';

export const EVIDENCE_LEVELS: readonly EvidenceLevel[] = ['A', 'B', 'C', 'D'];

export const isEvidenceLevel = (v: unknown): v is EvidenceLevel =>
  typeof v === 'string' &&
  (EVIDENCE_LEVELS as readonly string[]).includes(v);

/**
 * DocumentPhase — one phase as declared in the source.
 */
export interface DocumentPhase {
  readonly type: DocumentPhaseType;
  readonly durationMs: number;
  readonly curve?: DocumentCurveType;
}

/**
 * DocumentBreathConfig — breath-specific execution configuration.
 */
export interface DocumentBreathConfig {
  readonly cycles: number;
  readonly phases: readonly DocumentPhase[];
  readonly restBetweenCyclesMs?: number;
}

/**
 * DocumentMetadata — authorial / regulatory metadata preserved intact.
 *
 * The compiler does not interpret these fields. They pass through
 * to the IR and ExecutionPlan untouched so the application layer can
 * surface them in UI, regulatory reports, or audit logs.
 */
export interface DocumentMetadata {
  readonly author?: string;
  readonly language?: string;
  readonly references?: readonly string[];
  readonly evidenceLevel?: EvidenceLevel;
  readonly contraindications?: readonly string[];
  readonly category?: string;
  readonly tags?: readonly string[];
  readonly approvedAt?: Iso8601;
}

/**
 * ProtocolDocument — the parsed, structurally-valid document.
 *
 * Produced by JsonProtocolParser, consumed by validators, IR builder,
 * migration pipeline, and linter.
 */
export interface ProtocolDocument {
  readonly $schema: string;
  readonly id: ProtocolId;
  readonly version: SemanticVersion;
  readonly title: string;
  readonly subtitle?: string;
  readonly description?: string;
  readonly breath: DocumentBreathConfig;
  readonly metadata?: DocumentMetadata;
  readonly checksum?: string;
}

/**
 * Document construction helpers.
 */
export const DocumentPhase = (params: {
  type: DocumentPhaseType;
  durationMs: number;
  curve?: DocumentCurveType;
}): DocumentPhase => {
  const base: DocumentPhase = {
    type: params.type,
    durationMs: params.durationMs,
  };
  return params.curve !== undefined
    ? { ...base, curve: params.curve }
    : base;
};

/**
 * Checks whether a value is structurally a ProtocolDocument.
 * This is a permissive shape check — semantic validation happens later.
 */
export const isProtocolDocumentShape = (
  v: unknown,
): v is ProtocolDocument => {
  if (typeof v !== 'object' || v === null) return false;
  const doc = v as Record<string, unknown>;
  return (
    typeof doc['$schema'] === 'string' &&
    typeof doc['id'] === 'string' &&
    typeof doc['version'] === 'string' &&
    typeof doc['title'] === 'string' &&
    typeof doc['breath'] === 'object' &&
    doc['breath'] !== null &&
    Array.isArray((doc['breath'] as { phases?: unknown }).phases)
  );
};

/**
 * Type guard that returns true if the document has all required
 * metadata fields. Used by linter and validators.
 */
export const hasMetadata = (
  doc: ProtocolDocument,
): doc is ProtocolDocument & { metadata: DocumentMetadata } =>
  doc.metadata !== undefined;

/**
 * Returns the total declared duration of one cycle in ms.
 * Pure derivation from phases.
 */
export const computeDeclaredCycleMs = (
  breath: DocumentBreathConfig,
): number => {
  let total = 0;
  for (const p of breath.phases) {
    total += p.durationMs;
  }
  return total;
};

/**
 * Returns the total declared duration of the entire session in ms.
 */
export const computeDeclaredSessionMs = (
  breath: DocumentBreathConfig,
): Duration => {
  const cycleMs = computeDeclaredCycleMs(breath);
  const restMs = breath.restBetweenCyclesMs ?? 0;
  const cycles = Math.max(0, breath.cycles - 1);
  return (cycleMs * breath.cycles + restMs * cycles) as Duration;
};
