/**
 * AudioVolume — per-layer volume structure.
 *
 * All volumes are normalized to [0, 1] (linear). The effective
 * volume applied to a layer is `master × layer × (muted ? 0 : 1)`.
 * Conversion to dB / linear-amp is the adapter's responsibility —
 * the Engine speaks linear only.
 *
 *   { master, guidance, cue, ambient, music }
 *
 * The struct is deeply frozen.
 */

import type { AudioLayer } from './AudioLayer';
import { clamp01 } from '../util/volume-math';

export interface AudioVolumeMap {
  readonly master: number;
  readonly guidance: number;
  readonly cue: number;
  readonly ambient: number;
  readonly music: number;
}

export const DEFAULT_AUDIO_VOLUME: AudioVolumeMap = Object.freeze({
  master: 0.8,
  guidance: 0.9,
  cue: 0.7,
  ambient: 0.4,
  music: 0.5,
});

export const buildAudioVolumeMap = (
  master: number,
  perLayer: Partial<Record<AudioLayer, number>> = {},
): AudioVolumeMap => {
  const map: AudioVolumeMap = Object.freeze({
    master: clamp01(master),
    guidance: clamp01(perLayer.guidance ?? DEFAULT_AUDIO_VOLUME.guidance),
    cue: clamp01(perLayer.cue ?? DEFAULT_AUDIO_VOLUME.cue),
    ambient: clamp01(perLayer.ambient ?? DEFAULT_AUDIO_VOLUME.ambient),
    music: clamp01(perLayer.music ?? DEFAULT_AUDIO_VOLUME.music),
  });
  return map;
};

export const volumeForLayer = (map: AudioVolumeMap, layer: AudioLayer): number => {
  switch (layer) {
    case 'guidance':
      return map.guidance;
    case 'cue':
      return map.cue;
    case 'ambient':
      return map.ambient;
    case 'music':
      return map.music;
  }
};

export const setLayerVolume = (
  map: AudioVolumeMap,
  layer: AudioLayer,
  value: number,
): AudioVolumeMap => {
  const clamped = clamp01(value);
  switch (layer) {
    case 'guidance':
      return { ...map, guidance: clamped };
    case 'cue':
      return { ...map, cue: clamped };
    case 'ambient':
      return { ...map, ambient: clamped };
    case 'music':
      return { ...map, music: clamped };
  }
};

export const setMasterVolume = (map: AudioVolumeMap, value: number): AudioVolumeMap => ({
  ...map,
  master: clamp01(value),
});

export const isAudioVolumeMap = (v: unknown): v is AudioVolumeMap => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const m = v as Partial<AudioVolumeMap>;
  return (
    typeof m.master === 'number' &&
    typeof m.guidance === 'number' &&
    typeof m.cue === 'number' &&
    typeof m.ambient === 'number' &&
    typeof m.music === 'number'
  );
};