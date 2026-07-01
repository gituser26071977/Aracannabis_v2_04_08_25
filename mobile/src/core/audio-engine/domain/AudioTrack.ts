/**
 * AudioTrack — a named bundle of clips for one logical playback unit.
 *
 * A track is what `loadTrack(track)` accepts. It groups clips by
 * `layer` so the engine knows which asset to play when, e.g., a
 * "Diaphragmatic Breathing" track bundles:
 *
 *   - 1 ambient clip ("rain-soft")
 *   - 1 cue clip per phase (inhale/hold/exhale bells)
 *   - 1 guidance clip per phase per language
 *   - 1 optional music clip
 *
 * Tracks are frozen value objects. The Engine keeps the active track
 * reference and resolves clips lazily by id.
 */

import type { AudioClip } from './AudioClip';
import type { AudioLayer } from './AudioLayer';

export interface AudioTrack {
  readonly id: string;
  /** Optional human-readable title. */
  readonly title?: string;
  /** All clips that make up this track. */
  readonly clips: readonly AudioClip[];
  /** Optional per-layer "main" clip ids — preferred clip when layer is triggered. */
  readonly layerDefaults?: Readonly<Partial<Record<AudioLayer, string>>>;
}

export const buildAudioTrack = (
  id: string,
  clips: readonly AudioClip[],
  options: { title?: string; layerDefaults?: Readonly<Partial<Record<AudioLayer, string>>> } = {},
): AudioTrack => {
  const track: AudioTrack = Object.freeze({
    id,
    clips: Object.freeze(clips.map((c) => Object.freeze({ ...c }))),
    ...(options.title !== undefined ? { title: options.title } : {}),
    ...(options.layerDefaults !== undefined ? { layerDefaults: Object.freeze({ ...options.layerDefaults }) } : {}),
  });
  return track;
};

export const findClipById = (track: AudioTrack, clipId: string): AudioClip | null => {
  for (const c of track.clips) {
    if (c.id === clipId) {
      return c;
    }
  }
  return null;
};

export const clipsOfLayer = (track: AudioTrack, layer: AudioLayer): readonly AudioClip[] =>
  track.clips.filter((c) => c.layer === layer);

export const isAudioTrack = (v: unknown): v is AudioTrack => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const t = v as Partial<AudioTrack>;
  return typeof t.id === 'string' && Array.isArray(t.clips);
};