/**
 * @core/audio-engine — public barrel.
 *
 * Audio Engine v1.0.0 — synchronizes audio playback with the
 * AraFlow Core via Runtime events only. No timers of its own.
 *
 * Consumers go through `createAudioEngine(deps)` for the standard
 * facade, or import domain types directly when implementing an
 * `AudioAdapter` for a new backend.
 */

import { AudioEngine } from './application/AudioEngine';
import type { AudioEngineDeps } from './application/AudioEngineDeps';

export const createAudioEngine = (deps: AudioEngineDeps): AudioEngine =>
  new AudioEngine(deps);

// --- Application ---
export { AudioEngine } from './application/AudioEngine';
export type { AudioEngineDeps } from './application/AudioEngineDeps';
export { createAudioEventStream, type AudioEventStream } from './application/AudioEventStream';

// --- Domain types ---
export { type AudioLayer, AUDIO_LAYERS, isAudioLayer, labelForAudioLayer } from './domain/AudioLayer';
export { type AudioClip, buildAudioClip, isAudioClip } from './domain/AudioClip';
export {
  type AudioTrack,
  buildAudioTrack,
  findClipById,
  clipsOfLayer,
  isAudioTrack,
} from './domain/AudioTrack';
export {
  type AudioEngineState,
  AUDIO_ENGINE_STATES,
  TERMINAL_AUDIO_ENGINE_STATES,
  isAudioEngineState,
  isTerminalAudioEngineState,
  canAudioEngineTransition,
  labelForAudioEngineState,
} from './domain/AudioEngineState';
export {
  type AudioEvent,
  type AudioEventListener,
  type AudioUnsubscribe,
  type AudioEventType,
  AUDIO_EVENT_TYPES,
  isAudioEvent,
} from './domain/AudioEvent';
export {
  type AudioVolumeMap,
  DEFAULT_AUDIO_VOLUME,
  buildAudioVolumeMap,
  volumeForLayer,
  setLayerVolume,
  setMasterVolume,
  isAudioVolumeMap,
} from './domain/AudioVolume';
export {
  type AudioLanguage,
  AUDIO_LANGUAGES,
  isAudioLanguage,
  DEFAULT_AUDIO_LANGUAGE,
} from './domain/AudioLanguage';
export {
  type AudioAdapter,
  type AudioAdapterError,
  isAudioAdapter,
} from './domain/AudioAdapter';

// --- Utilities ---
export {
  clamp01,
  effectiveVolume,
  linearToDecibels,
  decibelsToLinear,
} from './util/volume-math';
export { phaseToCueEntry, phaseToCueId, phaseToGuidanceText } from './util/phase-to-cue';
export { DEFAULT_CUE_TABLE, type CueEntry, type CueTable } from './util/default-cue-table';

// --- Infra ---
export { createInMemoryAudioAdapter, InMemoryAudioAdapter } from './infra/InMemoryAudioAdapter';

// --- Version ---
export const AUDIO_ENGINE_VERSION = '1.0.0' as const;