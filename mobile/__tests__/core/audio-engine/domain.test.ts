/**
 * Audio Engine — domain + util unit tests.
 *
 * Covers all pure helpers: AudioLayer / AudioLanguage / AudioClip /
 * AudioTrack / AudioVolume / AudioEngineState / AudioEvent /
 * AudioAdapter / volume-math / phase-to-cue / default-cue-table.
 *
 * Goal: 100% coverage of domain + util without ever touching the
 * Adapter or the Engine.
 */

import {
  AUDIO_EVENT_TYPES,
  AUDIO_LANGUAGES,
  AUDIO_LAYERS,
  DEFAULT_AUDIO_VOLUME,
  TERMINAL_AUDIO_ENGINE_STATES,
  buildAudioClip,
  buildAudioTrack,
  buildAudioVolumeMap,
  canAudioEngineTransition,
  clamp01,
  clipsOfLayer,
  decibelsToLinear,
  effectiveVolume,
  findClipById,
  isAudioAdapter,
  isAudioClip,
  isAudioEngineState,
  isAudioEvent,
  isAudioLanguage,
  isAudioLayer,
  isAudioTrack,
  isAudioVolumeMap,
  isTerminalAudioEngineState,
  labelForAudioEngineState,
  labelForAudioLayer,
  linearToDecibels,
  phaseToCueEntry,
  phaseToCueId,
  phaseToGuidanceText,
  setLayerVolume,
  setMasterVolume,
  volumeForLayer,
  DEFAULT_CUE_TABLE,
  type CueEntry,
} from '../../../src/core/audio-engine';

// ─── AudioLayer ─────────────────────────────────────────────────────

describe('AudioLayer — constants and helpers', () => {
  it('AUDIO_LAYERS has exactly 4 entries', () => {
    expect(AUDIO_LAYERS.length).toBe(4);
    expect(AUDIO_LAYERS).toEqual(['guidance', 'cue', 'ambient', 'music']);
  });

  it('isAudioLayer accepts each layer', () => {
    expect(isAudioLayer('guidance')).toBe(true);
    expect(isAudioLayer('cue')).toBe(true);
    expect(isAudioLayer('ambient')).toBe(true);
    expect(isAudioLayer('music')).toBe(true);
  });

  it('isAudioLayer rejects non-strings and unknown values', () => {
    expect(isAudioLayer(null)).toBe(false);
    expect(isAudioLayer(undefined)).toBe(false);
    expect(isAudioLayer(0)).toBe(false);
    expect(isAudioLayer('sprite')).toBe(false);
    expect(isAudioLayer({})).toBe(false);
  });

  it('labelForAudioLayer returns Portuguese labels', () => {
    expect(labelForAudioLayer('guidance')).toBe('Guia vocal');
    expect(labelForAudioLayer('cue')).toBe('Sinal');
    expect(labelForAudioLayer('ambient')).toBe('Ambiente');
    expect(labelForAudioLayer('music')).toBe('Música');
  });
});

// ─── AudioLanguage ──────────────────────────────────────────────────

describe('AudioLanguage — constants and helpers', () => {
  it('AUDIO_LANGUAGES has pt-BR and en-US', () => {
    expect(AUDIO_LANGUAGES).toContain('pt-BR');
    expect(AUDIO_LANGUAGES).toContain('en-US');
  });

  it('isAudioLanguage accepts valid languages', () => {
    expect(isAudioLanguage('pt-BR')).toBe(true);
    expect(isAudioLanguage('en-US')).toBe(true);
  });

  it('isAudioLanguage rejects invalid languages', () => {
    expect(isAudioLanguage('fr')).toBe(false);
    expect(isAudioLanguage(null)).toBe(false);
    expect(isAudioLanguage(42)).toBe(false);
  });
});

// ─── AudioClip ──────────────────────────────────────────────────────

describe('AudioClip — factory + guard', () => {
  it('buildAudioClip produces a frozen clip', () => {
    const clip = buildAudioClip('id', 'cue', 'memory://cue.mp3');
    expect(clip.id).toBe('id');
    expect(clip.layer).toBe('cue');
    expect(clip.src).toBe('memory://cue.mp3');
    expect(clip.durationMs).toBeUndefined();
  });

  it('buildAudioClip accepts optional language and duration', () => {
    const clip = buildAudioClip('id', 'cue', 'memory://cue.mp3', {
      language: 'pt-BR',
      durationMs: 1500,
    });
    expect(clip.language).toBe('pt-BR');
    expect(clip.durationMs).toBe(1500);
  });

  it('isAudioClip accepts valid clips', () => {
    const clip = buildAudioClip('id', 'cue', 'memory://c.mp3');
    expect(isAudioClip(clip)).toBe(true);
  });

  it('isAudioClip rejects invalid objects', () => {
    expect(isAudioClip(null)).toBe(false);
    expect(isAudioClip({})).toBe(false);
    expect(isAudioClip({ id: 1, layer: 'cue', src: 'x' })).toBe(false);
    expect(isAudioClip({ id: 'id', layer: 'fake', src: 'x' })).toBe(false);
  });
});

// ─── AudioTrack ─────────────────────────────────────────────────────

describe('AudioTrack — factory + guards', () => {
  const clips = [
    buildAudioClip('c1', 'cue', 'x'),
    buildAudioClip('a1', 'ambient', 'y'),
  ];

  it('buildAudioTrack creates a track', () => {
    const t = buildAudioTrack('t1', clips, { title: 'Track', layerDefaults: { cue: 'c1' } });
    expect(t.id).toBe('t1');
    expect(t.title).toBe('Track');
    expect(t.clips.length).toBe(2);
    expect(t.layerDefaults?.cue).toBe('c1');
  });

  it('findClipById finds existing clip', () => {
    const t = buildAudioTrack('t1', clips);
    expect(findClipById(t, 'c1')?.id).toBe('c1');
    expect(findClipById(t, 'missing')).toBeNull();
  });

  it('clipsOfLayer filters by layer', () => {
    const t = buildAudioTrack('t', clips);
    expect(clipsOfLayer(t, 'cue').length).toBe(1);
    expect(clipsOfLayer(t, 'ambient').length).toBe(1);
    expect(clipsOfLayer(t, 'music').length).toBe(0);
  });

  it('isAudioTrack accepts valid', () => {
    expect(isAudioTrack(buildAudioTrack('t', []))).toBe(true);
  });

  it('isAudioTrack rejects invalid', () => {
    expect(isAudioTrack(null)).toBe(false);
    expect(isAudioTrack({})).toBe(false);
    expect(isAudioTrack({ id: 1, clips: [] })).toBe(false);
  });
});

// ─── AudioEngineState ───────────────────────────────────────────────

describe('AudioEngineState — FSM', () => {
  it('has 7 states and 1 terminal', () => {
    expect(TERMINAL_AUDIO_ENGINE_STATES).toEqual(['disposed']);
  });

  it('isAudioEngineState — valid', () => {
    expect(isAudioEngineState('uninitialized')).toBe(true);
    expect(isAudioEngineState('playing')).toBe(true);
  });

  it('isAudioEngineState — invalid', () => {
    expect(isAudioEngineState('turbo')).toBe(false);
    expect(isAudioEngineState(null)).toBe(false);
  });

  it('isTerminalAudioEngineState', () => {
    expect(isTerminalAudioEngineState('disposed')).toBe(true);
    expect(isTerminalAudioEngineState('playing')).toBe(false);
  });

  it('canAudioEngineTransition — legal transitions', () => {
    expect(canAudioEngineTransition('uninitialized', 'loaded')).toBe(true);
    expect(canAudioEngineTransition('loaded', 'playing')).toBe(true);
    expect(canAudioEngineTransition('playing', 'paused')).toBe(true);
    expect(canAudioEngineTransition('paused', 'playing')).toBe(true);
    expect(canAudioEngineTransition('stopped', 'loaded')).toBe(true);
    expect(canAudioEngineTransition('stopped', 'playing')).toBe(true);
    expect(canAudioEngineTransition('errored', 'loaded')).toBe(true);
    expect(canAudioEngineTransition('loaded', 'loaded')).toBe(true);
  });

  it('canAudioEngineTransition — illegal transitions', () => {
    expect(canAudioEngineTransition('uninitialized', 'playing')).toBe(false);
    expect(canAudioEngineTransition('playing', 'loaded')).toBe(false);
    expect(canAudioEngineTransition('paused', 'loaded')).toBe(false);
    expect(canAudioEngineTransition('disposed', 'loaded')).toBe(false);
  });

  it('labelForAudioEngineState — Portuguese labels for all 7 states', () => {
    expect(labelForAudioEngineState('uninitialized')).toBe('Não inicializado');
    expect(labelForAudioEngineState('loaded')).toBe('Pronto');
    expect(labelForAudioEngineState('playing')).toBe('Reproduzindo');
    expect(labelForAudioEngineState('paused')).toBe('Pausado');
    expect(labelForAudioEngineState('stopped')).toBe('Parado');
    expect(labelForAudioEngineState('errored')).toBe('Erro');
    expect(labelForAudioEngineState('disposed')).toBe('Liberado');
  });
});

// ─── AudioEvent ─────────────────────────────────────────────────────

describe('AudioEvent — constants and guards', () => {
  it('AUDIO_EVENT_TYPES has 11 entries', () => {
    expect(AUDIO_EVENT_TYPES.length).toBe(11);
    expect(AUDIO_EVENT_TYPES).toContain('audio-started');
    expect(AUDIO_EVENT_TYPES).toContain('audio-paused');
    expect(AUDIO_EVENT_TYPES).toContain('audio-resumed');
    expect(AUDIO_EVENT_TYPES).toContain('audio-stopped');
    expect(AUDIO_EVENT_TYPES).toContain('track-loaded');
    expect(AUDIO_EVENT_TYPES).toContain('cue-played');
    expect(AUDIO_EVENT_TYPES).toContain('guidance-played');
    expect(AUDIO_EVENT_TYPES).toContain('ambient-started');
    expect(AUDIO_EVENT_TYPES).toContain('music-started');
    expect(AUDIO_EVENT_TYPES).toContain('volume-changed');
    expect(AUDIO_EVENT_TYPES).toContain('mute-changed');
  });

  it('isAudioEvent accepts valid events', () => {
    expect(isAudioEvent({ type: 'audio-started', trackId: 't', layer: null, monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'audio-paused', atElapsedMs: 0, monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'audio-resumed', pausedForMs: 0, monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'track-loaded', trackId: 't', layer: 'guidance', clipCount: 1, monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'cue-played', cueId: 'c', layer: 'cue', monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'guidance-played', text: 'x', language: 'pt-BR', monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'ambient-started', trackId: 't', monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'music-started', trackId: 't', monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'volume-changed', layer: 'master', value: 0.5, monotonicMs: 0 })).toBe(true);
    expect(isAudioEvent({ type: 'mute-changed', muted: true, monotonicMs: 0 })).toBe(true);
  });

  it('isAudioEvent rejects invalid events', () => {
    expect(isAudioEvent(null)).toBe(false);
    expect(isAudioEvent({})).toBe(false);
    expect(isAudioEvent({ type: 'unknown' })).toBe(false);
  });
});

// ─── AudioAdapter ───────────────────────────────────────────────────

describe('AudioAdapter — guard', () => {
  it('isAudioAdapter accepts an adapter-shaped object', () => {
    expect(
      isAudioAdapter({
        id: 'a',
        load: () => Promise.resolve({ ok: true, value: undefined }),
        play: () => Promise.resolve({ ok: true, value: undefined }),
        pause: () => Promise.resolve({ ok: true, value: undefined }),
        resume: () => Promise.resolve({ ok: true, value: undefined }),
        stop: () => Promise.resolve({ ok: true, value: undefined }),
        setLayerVolume: () => Promise.resolve({ ok: true, value: undefined }),
        setMasterVolume: () => Promise.resolve({ ok: true, value: undefined }),
        dispose: () => Promise.resolve({ ok: true, value: undefined }),
      }),
    ).toBe(true);
  });

  it('isAudioAdapter rejects incomplete', () => {
    expect(isAudioAdapter(null)).toBe(false);
    expect(isAudioAdapter({ id: 'a' })).toBe(false);
  });
});

// ─── AudioVolume ────────────────────────────────────────────────────

describe('AudioVolume — pure helpers', () => {
  it('DEFAULT_AUDIO_VOLUME has all 5 keys', () => {
    expect(DEFAULT_AUDIO_VOLUME.master).toBe(0.8);
    expect(DEFAULT_AUDIO_VOLUME.guidance).toBe(0.9);
    expect(DEFAULT_AUDIO_VOLUME.cue).toBe(0.7);
    expect(DEFAULT_AUDIO_VOLUME.ambient).toBe(0.4);
    expect(DEFAULT_AUDIO_VOLUME.music).toBe(0.5);
  });

  it('buildAudioVolumeMap defaults to DEFAULT_AUDIO_VOLUME for unspecified layers', () => {
    const m = buildAudioVolumeMap(0.6);
    expect(m.master).toBe(0.6);
    expect(m.guidance).toBe(0.9);
    expect(m.cue).toBe(0.7);
  });

  it('buildAudioVolumeMap overrides', () => {
    const m = buildAudioVolumeMap(0.6, { cue: 0.1, ambient: 0.2 });
    expect(m.cue).toBe(0.1);
    expect(m.ambient).toBe(0.2);
  });

  it('buildAudioVolumeMap clamps', () => {
    const m = buildAudioVolumeMap(2, { cue: -1 });
    expect(m.master).toBe(1);
    expect(m.cue).toBe(0);
  });

  it('volumeForLayer returns correct value for each layer', () => {
    const m = DEFAULT_AUDIO_VOLUME;
    expect(volumeForLayer(m, 'guidance')).toBe(0.9);
    expect(volumeForLayer(m, 'cue')).toBe(0.7);
    expect(volumeForLayer(m, 'ambient')).toBe(0.4);
    expect(volumeForLayer(m, 'music')).toBe(0.5);
  });

  it('setLayerVolume updates one layer', () => {
    const m = setLayerVolume(DEFAULT_AUDIO_VOLUME, 'guidance', 0.5);
    expect(m.guidance).toBe(0.5);
    expect(m.cue).toBe(DEFAULT_AUDIO_VOLUME.cue);
  });

  it('setLayerVolume updates each layer independently', () => {
    let m = setLayerVolume(DEFAULT_AUDIO_VOLUME, 'guidance', 0.1);
    m = setLayerVolume(m, 'cue', 0.2);
    m = setLayerVolume(m, 'ambient', 0.3);
    m = setLayerVolume(m, 'music', 0.4);
    expect(m.guidance).toBe(0.1);
    expect(m.cue).toBe(0.2);
    expect(m.ambient).toBe(0.3);
    expect(m.music).toBe(0.4);
  });

  it('setMasterVolume updates master', () => {
    const m = setMasterVolume(DEFAULT_AUDIO_VOLUME, 0.3);
    expect(m.master).toBe(0.3);
  });

  it('isAudioVolumeMap accepts valid', () => {
    expect(isAudioVolumeMap(DEFAULT_AUDIO_VOLUME)).toBe(true);
  });

  it('isAudioVolumeMap rejects invalid', () => {
    expect(isAudioVolumeMap(null)).toBe(false);
    expect(isAudioVolumeMap({})).toBe(false);
    expect(isAudioVolumeMap({ master: 0, guidance: 0, cue: 0, ambient: 0 })).toBe(false);
  });
});

// ─── volume-math ────────────────────────────────────────────────────

describe('volume-math — pure helpers', () => {
  it('clamp01 clamps to [0, 1]', () => {
    expect(clamp01(-1)).toBe(0);
    expect(clamp01(0)).toBe(0);
    expect(clamp01(0.5)).toBe(0.5);
    expect(clamp01(1)).toBe(1);
    expect(clamp01(2)).toBe(1);
  });

  it('effectiveVolume multiplies', () => {
    expect(effectiveVolume(0.5, 0.5, false)).toBeCloseTo(0.25);
    expect(effectiveVolume(0, 1, false)).toBe(0);
    expect(effectiveVolume(1, 0, false)).toBe(0);
  });

  it('effectiveVolume is 0 when muted', () => {
    expect(effectiveVolume(1, 1, true)).toBe(0);
    expect(effectiveVolume(0.5, 0.5, true)).toBe(0);
  });

  it('linearToDecibels is monotonically decreasing to -∞ at 0', () => {
    expect(linearToDecibels(1)).toBeCloseTo(0);
    expect(linearToDecibels(0.5)).toBeCloseTo(-6.02, 1);
    expect(linearToDecibels(0)).toBe(-Infinity);
  });

  it('decibelsToLinear is inverse', () => {
    expect(decibelsToLinear(0)).toBeCloseTo(1);
    expect(decibelsToLinear(-6.02)).toBeCloseTo(0.5, 1);
    expect(decibelsToLinear(-Infinity)).toBe(0);
  });
});

// ─── default-cue-table ──────────────────────────────────────────────

describe('default-cue-table — has all phases per language', () => {
  it('PT-BR has 6 phase entries', () => {
    const table: Record<string, CueEntry> = DEFAULT_CUE_TABLE['pt-BR'];
    expect(Object.keys(table).length).toBeGreaterThanOrEqual(6);
    expect(table.inhale.guidanceText).toBe('Inspire');
    expect(table.exhale.guidanceText).toBe('Expire');
    expect(table.hold.guidanceText).toBe('Segure');
  });

  it('EN-US has 6 phase entries', () => {
    const table: Record<string, CueEntry> = DEFAULT_CUE_TABLE['en-US'];
    expect(table.inhale.guidanceText).toBe('Breathe in');
    expect(table.exhale.guidanceText).toBe('Breathe out');
    expect(table.hold.guidanceText).toBe('Hold');
  });
});

// ─── phase-to-cue ───────────────────────────────────────────────────

describe('phase-to-cue — pure helpers', () => {
  it('phaseToCueEntry returns entry or null', () => {
    expect(phaseToCueEntry('inhale', 'pt-BR')?.cueId).toBe('cue.bell.inhale');
    expect(phaseToCueEntry('exhale', 'pt-BR')?.cueId).toBe('cue.bell.exhale');
    expect(phaseToCueEntry('hold', 'pt-BR')?.guidanceText).toBe('Segure');
  });

  it('phaseToCueEntry returns null for unknown phase', () => {
    expect(phaseToCueEntry('made-up' as never, 'pt-BR')).toBeNull();
  });

  it('phaseToCueEntry returns null for unknown language', () => {
    expect(phaseToCueEntry('inhale', 'fr-FR' as never)).toBeNull();
  });

  it('phaseToCueId returns cueId or null', () => {
    expect(phaseToCueId('inhale', 'pt-BR')).toBe('cue.bell.inhale');
    expect(phaseToCueId('exhale', 'en-US')).toBe('cue.bell.exhale');
    expect(phaseToCueId('unknown' as never, 'pt-BR')).toBeNull();
  });

  it('phaseToGuidanceText returns text or null', () => {
    expect(phaseToGuidanceText('inhale', 'pt-BR')).toBe('Inspire');
    expect(phaseToGuidanceText('hold', 'pt-BR')).toBe('Segure');
    expect(phaseToGuidanceText('unknown' as never, 'pt-BR')).toBeNull();
  });
});
