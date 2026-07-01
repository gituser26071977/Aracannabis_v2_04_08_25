/**
 * AudioClip — an immutable reference to a single audio asset.
 *
 * `id` is the canonical identifier used by the AudioAdapter to
 * resolve and play the asset. `src` is an opaque handle (URL, file
 * path, asset id, TTS payload) interpreted by the adapter — the
 * Engine never inspects it.
 *
 * Clips are deeply frozen value objects.
 */

import type { AudioLayer } from './AudioLayer';
import type { AudioLanguage } from './AudioLanguage';

export interface AudioClip {
  readonly id: string;
  readonly layer: AudioLayer;
  readonly src: string;
  /** Optional: when `layer === 'guidance'`, the language of the phrase. */
  readonly language?: AudioLanguage;
  /** Optional: nominal duration in ms (advisory only — Engine never relies on it). */
  readonly durationMs?: number;
}

export const buildAudioClip = (
  id: string,
  layer: AudioLayer,
  src: string,
  options: { language?: AudioLanguage; durationMs?: number } = {},
): AudioClip => {
  const clip: AudioClip = Object.freeze({
    id,
    layer,
    src,
    ...(options.language !== undefined ? { language: options.language } : {}),
    ...(options.durationMs !== undefined ? { durationMs: options.durationMs } : {}),
  });
  return clip;
};

export const isAudioClip = (v: unknown): v is AudioClip => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const c = v as Partial<AudioClip>;
  return (
    typeof c.id === 'string' &&
    typeof c.src === 'string' &&
    typeof c.layer === 'string' &&
    (c.layer === 'guidance' || c.layer === 'cue' || c.layer === 'ambient' || c.layer === 'music')
  );
};