/**
 * Document phase type — names used in the JSON document.
 *
 * Maps 1:1 to the canonical BreathPhase in shared-contracts, but uses
 * the short names that are friendly in JSON. The IR builder performs
 * the mapping.
 */

import { isBreathPhase, type BreathPhase } from '@araflow/shared-contracts';

export const DOCUMENT_PHASE_TYPES = [
  'inhale',
  'hold-in',
  'exhale',
  'hold-out',
] as const;

export type DocumentPhaseType = (typeof DOCUMENT_PHASE_TYPES)[number];

export const isDocumentPhaseType = (
  v: unknown,
): v is DocumentPhaseType =>
  typeof v === 'string' &&
  (DOCUMENT_PHASE_TYPES as readonly string[]).includes(v);

/**
 * Maps a document phase type to the canonical BreathPhase used by engines.
 */
export const toCanonicalPhase = (
  doc: DocumentPhaseType,
): BreathPhase => {
  switch (doc) {
    case 'inhale':
      return 'inhaling';
    case 'hold-in':
      return 'holdAfterInhale';
    case 'exhale':
      return 'exhaling';
    case 'hold-out':
      return 'holdAfterExhale';
    default:
      throw new Error(`Unknown document phase type: ${String(doc)}`);
  }
};

export const fromCanonicalPhase = (
  phase: BreathPhase,
): DocumentPhaseType => {
  switch (phase) {
    case 'inhaling':
      return 'inhale';
    case 'holdAfterInhale':
      return 'hold-in';
    case 'exhaling':
      return 'exhale';
    case 'holdAfterExhale':
      return 'hold-out';
    default:
      throw new Error(`Unknown canonical BreathPhase: ${String(phase)}`);
  }
};

/**
 * Exhaustiveness guard for BreathPhase from shared-contracts.
 * If a new phase is added there, this fails to compile, prompting an
 * update to the mapping above.
 */
export const _exhaustiveBreathPhase = (phase: BreathPhase): DocumentPhaseType => {
  if (!isBreathPhase(phase)) {
    throw new Error(`Unknown BreathPhase: ${String(phase)}`);
  }
  return fromCanonicalPhase(phase);
};
