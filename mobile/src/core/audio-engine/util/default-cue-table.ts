/**
 * default-cue-table — default cue IDs per phase per language.
 *
 * Pure data. No imports of UI / RN. Sprint 10 ships only PT-BR and
 * EN-US. The IDs are pure strings; no audio files are bundled. The
 * `InMemoryAudioAdapter` (mock) records the request; a real backend
 * will resolve the ID against an asset bundle.
 *
 * Cue IDs follow the convention `cue.<family>.<variant>` so future
 * backends can route by prefix.
 */

import type { AnimationPhase } from '@core/animation-engine';

import type { AudioLanguage } from '../domain/AudioLanguage';

export interface CueEntry {
  readonly cueId: string;
  readonly guidanceText: string;
}

export type CueTable = Readonly<Record<AnimationPhase, CueEntry>>;

const PT_BR_TABLE: CueTable = Object.freeze({
  idle: Object.freeze({ cueId: 'cue.silence', guidanceText: '' }),
  preparing: Object.freeze({ cueId: 'cue.bell.soft', guidanceText: 'Prepare-se' }),
  inhale: Object.freeze({ cueId: 'cue.bell.inhale', guidanceText: 'Inspire' }),
  hold: Object.freeze({ cueId: 'cue.bell.hold', guidanceText: 'Segure' }),
  exhale: Object.freeze({ cueId: 'cue.bell.exhale', guidanceText: 'Expire' }),
  completed: Object.freeze({ cueId: 'cue.bell.end', guidanceText: 'Concluído' }),
});

const EN_US_TABLE: CueTable = Object.freeze({
  idle: Object.freeze({ cueId: 'cue.silence', guidanceText: '' }),
  preparing: Object.freeze({ cueId: 'cue.bell.soft', guidanceText: 'Get ready' }),
  inhale: Object.freeze({ cueId: 'cue.bell.inhale', guidanceText: 'Breathe in' }),
  hold: Object.freeze({ cueId: 'cue.bell.hold', guidanceText: 'Hold' }),
  exhale: Object.freeze({ cueId: 'cue.bell.exhale', guidanceText: 'Breathe out' }),
  completed: Object.freeze({ cueId: 'cue.bell.end', guidanceText: 'Complete' }),
});

export const DEFAULT_CUE_TABLE: Readonly<Record<AudioLanguage, CueTable>> = Object.freeze({
  'pt-BR': PT_BR_TABLE,
  'en-US': EN_US_TABLE,
});