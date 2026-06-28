/**
 * IRBuilder — converts a structurally-valid ProtocolDocument into the
 * canonical ProtocolIR.
 *
 * Responsibilities:
 *   - Translate document phase types to canonical BreathPhase
 *   - Translate document curve types to canonical CurveType
 *   - Pre-calculate per-phase ratios
 *   - Pre-calculate total cycle and session durations
 *   - Preserve metadata fields INTACT (no interpretation)
 *   - Stamp compiledAt (canonical ISO 8601)
 *
 * Pure function. No I/O. No side effects.
 */

import {
  Duration,
  Iso8601,
  Iso8601FromTimestamp,
  PhaseIndex,
  TimestampNow,
  type Iso8601 as Iso8601Type,
} from '@araflow/shared-contracts';

import type { ProtocolDocument } from '../domain/ProtocolDocument';
import type {
  ProtocolIR,
  BreathConfigIR,
  PhaseIR,
  MetadataIR,
} from '../domain/IntermediateRepresentation';
import { emptyMetadataIR } from '../domain/IntermediateRepresentation';
import { toCanonicalPhase } from '../domain/DocumentPhaseType';
import { toCanonicalCurve } from '../domain/DocumentCurve';

/**
 * Builds a ProtocolIR from a ProtocolDocument.
 *
 * Throws AppError only for programmer errors (invariant violations),
 * not for user input. User-input errors should have been caught by
 * validators.
 */
export const buildIR = (
  doc: ProtocolDocument,
  now: () => number = Date.now,
): ProtocolIR => {
  // Phases: map to canonical + compute ratios
  const totalCycleMs = sumPhaseDurations(doc);
  const phases: PhaseIR[] = doc.breath.phases.map((p, i) => {
    const canonicalPhase = toCanonicalPhase(p.type);
    const canonicalCurve =
      p.curve !== undefined ? toCanonicalCurve(p.curve) : 'easeInOut';
    const ratio = totalCycleMs > 0 ? p.durationMs / totalCycleMs : 0;
    const ir: PhaseIR = {
      index: i as unknown as PhaseIndex,
      phase: canonicalPhase,
      duration: p.durationMs as unknown as Duration,
      curve: canonicalCurve,
      ratio,
    };
    return ir;
  });

  // Rest between cycles
  const restMs = doc.breath.restBetweenCyclesMs ?? 0;

  // Total session
  const totalSessionMs =
    totalCycleMs * doc.breath.cycles + restMs * Math.max(0, doc.breath.cycles - 1);

  const breath: BreathConfigIR = Object.freeze({
    cycles: doc.breath.cycles,
    phases: Object.freeze(phases),
    restBetweenCyclesMs: restMs as unknown as Duration,
    totalCycleMs: totalCycleMs as unknown as Duration,
    totalSessionMs: totalSessionMs as unknown as Duration,
  });

  // Metadata — preserved intact, no interpretation
  const metadata: MetadataIR = buildMetadata(doc);

  const ir: ProtocolIR = Object.freeze({
    id: doc.id,
    version: doc.version,
    title: doc.title,
    subtitle: doc.subtitle ?? '',
    description: doc.description ?? '',
    metadata,
    breath,
    compiledAt: compileStamp(now),
  });

  return ir;
};

/**
 * Builds the metadata IR, preserving all fields from the document.
 */
export const buildMetadata = (doc: ProtocolDocument): MetadataIR => {
  const md = doc.metadata;
  if (md === undefined) {
    return Object.freeze(emptyMetadataIR());
  }
  const out: MetadataIR = {
    references: Object.freeze([...(md.references ?? [])]),
    contraindications: Object.freeze([...(md.contraindications ?? [])]),
    tags: Object.freeze([...(md.tags ?? [])]),
  };
  if (md.author !== undefined) (out as { author?: string }).author = md.author;
  if (md.language !== undefined) (out as { language?: string }).language = md.language;
  if (md.evidenceLevel !== undefined)
    (out as { evidenceLevel?: string }).evidenceLevel = md.evidenceLevel;
  if (md.category !== undefined) (out as { category?: string }).category = md.category;
  if (md.approvedAt !== undefined) (out as { approvedAt?: Iso8601Type }).approvedAt = md.approvedAt;
  return Object.freeze(out);
};

const sumPhaseDurations = (doc: ProtocolDocument): number => {
  let sum = 0;
  for (const p of doc.breath.phases) sum += p.durationMs;
  return sum;
};

const compileStamp = (now: () => number): Iso8601Type => {
  const ts = TimestampNow(now);
  return Iso8601FromTimestamp(ts);
};

// Re-exports for callers that may need Iso8601
export { Iso8601 };
