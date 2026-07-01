/**
 * phase-to-cue — pure lookup: AnimationPhase + AudioLanguage → CueEntry.
 *
 * Returns `null` if the language is unknown (defensive — language is
 * already validated by the type system at construction). Returns the
 * table entry as-is when present (no transformation), so callers can
 * dispatch on `cueId` and forward `guidanceText` to the guidance layer.
 */

import type { AnimationPhase } from '@core/animation-engine';

import type { AudioLanguage } from '../domain/AudioLanguage';
import { DEFAULT_CUE_TABLE, type CueEntry } from './default-cue-table';

export const phaseToCueEntry = (
  phase: AnimationPhase,
  language: AudioLanguage,
): CueEntry | null => {
  const table = DEFAULT_CUE_TABLE[language];
  if (table === undefined) {
    return null;
  }
  const entry = table[phase];
  return entry ?? null;
};

/** Convenience: just the cue id, dropping the guidance text. */
export const phaseToCueId = (phase: AnimationPhase, language: AudioLanguage): string | null => {
  const entry = phaseToCueEntry(phase, language);
  return entry === null ? null : entry.cueId;
};

/** Convenience: just the guidance text. */
export const phaseToGuidanceText = (
  phase: AnimationPhase,
  language: AudioLanguage,
): string | null => {
  const entry = phaseToCueEntry(phase, language);
  return entry === null ? null : entry.guidanceText;
};