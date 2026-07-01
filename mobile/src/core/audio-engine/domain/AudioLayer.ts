/**
 * AudioLayer — the four orthogonal audio layers of a session.
 *
 * Every audio asset belongs to exactly one layer. Layers can be
 * enabled/disabled individually via volumes and the `muted` flag.
 *
 *   - 'guidance': spoken phrases ("Inspire", "Segure", "Expire").
 *   - 'cue':      short percussive markers (bell, click, breath cue).
 *   - 'ambient':  background textures (rain, ocean, white noise).
 *   - 'music':    foreground musical tracks (pads, drones).
 */

export type AudioLayer = 'guidance' | 'cue' | 'ambient' | 'music';

export const AUDIO_LAYERS: readonly AudioLayer[] = [
  'guidance',
  'cue',
  'ambient',
  'music',
] as const;

export const isAudioLayer = (v: unknown): v is AudioLayer =>
  typeof v === 'string' && (AUDIO_LAYERS as readonly string[]).includes(v);

/** Human-readable label for the layer (Portuguese). */
export const labelForAudioLayer = (layer: AudioLayer): string => {
  switch (layer) {
    case 'guidance':
      return 'Guia vocal';
    case 'cue':
      return 'Sinal';
    case 'ambient':
      return 'Ambiente';
    case 'music':
      return 'Música';
  }
};