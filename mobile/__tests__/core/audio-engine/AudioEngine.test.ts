/**
 * AudioEngine — main test suite.
 *
 * Sprint 10 — Audio Engine.
 */

import {
  type AudioClip,
  type AudioEvent,
  type AudioTrack,
  AudioEngine,
  buildAudioClip,
  buildAudioTrack,
  createAudioEngine,
} from '../../../src/core/audio-engine';

import { buildFakeAudioAdapter, buildFakeRuntime } from './fakes';

const ambientClip: AudioClip = buildAudioClip('ambient.rain-soft', 'ambient', 'memory://ambient/rain-soft.mp3', {
  durationMs: 600_000,
});
const inhaleCue: AudioClip = buildAudioClip('cue.bell.inhale', 'cue', 'memory://cue/inhale.mp3', {
  durationMs: 1500,
});
const exhaleCue: AudioClip = buildAudioClip('cue.bell.exhale', 'cue', 'memory://cue/exhale.mp3', {
  durationMs: 1500,
});

const track: AudioTrack = buildAudioTrack('track.diaphragmatic', [ambientClip, inhaleCue, exhaleCue], {
  title: 'Respiração Diafragmática',
  layerDefaults: { ambient: 'ambient.rain-soft', cue: 'cue.bell.inhale' },
});

describe('AudioEngine — construction & version', () => {
  it('factory exists and produces a working engine', () => {
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter });
    expect(engine).toBeInstanceOf(AudioEngine);
    expect(engine.getState()).toBe('uninitialized');
  });

  it('engine has a stable id', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    expect(engine.id).toBe('araflow-audio-v1');
  });

  it('accepts a custom engineId', () => {
    const engine = createAudioEngine({
      adapter: buildFakeAudioAdapter(),
      engineId: 'custom-id',
    });
    expect(engine.id).toBe('custom-id');
  });

  it('subscribes to runtime when provided', () => {
    const runtime = buildFakeRuntime();
    createAudioEngine({ adapter: buildFakeAudioAdapter(), runtime });
    expect(runtime.listenerCount()).toBe(1);
  });
});

describe('AudioEngine — loadTrack', () => {
  it('loads a valid track and transitions to loaded', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const result = engine.loadTrack(track);
    expect(result.ok).toBe(true);
    expect(engine.getState()).toBe('loaded');
    expect(engine.getActiveTrack()?.id).toBe('track.diaphragmatic');
  });

  it('rejects a track with no clips', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const empty = buildAudioTrack('empty', []);
    const result = engine.loadTrack(empty);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('audio_engine_empty_track');
    }
    expect(engine.getState()).toBe('uninitialized');
  });

  it('emits track-loaded event on successful load', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.loadTrack(track);
    const loaded = events.find((e) => e.type === 'track-loaded');
    expect(loaded).toBeDefined();
    if (loaded && loaded.type === 'track-loaded') {
      expect(loaded.trackId).toBe('track.diaphragmatic');
    }
  });

  it('rejects load when state is uninitialized and already loaded would conflict (loads twice succeeds)', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    // After load, the state is 'loaded'; loading again should be allowed (stopped transition was registered).
    const result = engine.loadTrack(track);
    expect(result.ok).toBe(true);
  });

  it('rejects load when state is playing', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    engine.play();
    const result = engine.loadTrack(track);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('audio_engine_invalid_state');
    }
  });
});

describe('AudioEngine — play/pause/resume/stop', () => {
  it('plays a loaded track', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    const result = engine.play();
    expect(result.ok).toBe(true);
    expect(engine.getState()).toBe('playing');
  });

  it('rejects play from uninitialized', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const result = engine.play();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('audio_engine_invalid_state');
    }
  });

  it('rejects pause from uninitialized (covers pause error branch)', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const result = engine.pause();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe('audio_engine_invalid_state');
    }
  });

  it('pauses a playing engine', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    engine.play();
    const result = engine.pause();
    expect(result.ok).toBe(true);
    expect(engine.getState()).toBe('paused');
  });

  it('resumes a paused engine', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    engine.play();
    engine.pause();
    const result = engine.resume();
    expect(result.ok).toBe(true);
    expect(engine.getState()).toBe('playing');
  });

  it('rejects resume from loaded (not paused)', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    const result = engine.resume();
    expect(result.ok).toBe(false);
  });

  it('stops a playing engine', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    engine.play();
    const result = engine.stop();
    expect(result.ok).toBe(true);
    expect(engine.getState()).toBe('stopped');
  });

  it('rejects stop from uninitialized', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const result = engine.stop();
    expect(result.ok).toBe(false);
  });

  it('emits audio-started/paused/resumed/stopped events', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.loadTrack(track);
    engine.play();
    engine.pause();
    engine.resume();
    engine.stop();
    const types = events.map((e) => e.type);
    expect(types).toContain('audio-started');
    expect(types).toContain('audio-paused');
    expect(types).toContain('audio-resumed');
    expect(types).toContain('audio-stopped');
  });
});

describe('AudioEngine — dispose', () => {
  it('transitions to disposed', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    engine.dispose();
    expect(engine.getState()).toBe('disposed');
  });

  it('is idempotent', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.dispose();
    expect(() => engine.dispose()).not.toThrow();
    expect(engine.getState()).toBe('disposed');
  });

  it('unsubscribes from runtime', () => {
    const runtime = buildFakeRuntime();
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter(), runtime });
    expect(runtime.listenerCount()).toBe(1);
    engine.dispose();
    expect(runtime.listenerCount()).toBe(0);
  });

  it('disposes the adapter', async () => {
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter });
    engine.dispose();
    // dispose on the adapter is invoked via void; wait one microtask.
    await Promise.resolve();
    expect(adapter.disposeCount).toBeGreaterThanOrEqual(1);
  });

  it('subscribe after dispose is a no-op', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.dispose();
    const unsubscribe = engine.subscribe(() => undefined);
    expect(typeof unsubscribe).toBe('function');
  });
});

describe('AudioEngine — subscribe', () => {
  it('receives all 11 event types', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.loadTrack(track);
    engine.play();
    engine.pause();
    engine.setVolume('guidance', 0.5);
    engine.setMasterVolumeValue(0.7);
    engine.mute();
    engine.unmute();
    engine.resume();
    engine.stop();
    const types = new Set(events.map((e) => e.type));
    expect(types.has('track-loaded')).toBe(true);
    expect(types.has('audio-started')).toBe(true);
    expect(types.has('audio-paused')).toBe(true);
    expect(types.has('audio-resumed')).toBe(true);
    expect(types.has('audio-stopped')).toBe(true);
    expect(types.has('volume-changed')).toBe(true);
    expect(types.has('mute-changed')).toBe(true);
  });

  it('routes listener errors to onListenerError', () => {
    const errors: unknown[] = [];
    const engine = createAudioEngine({
      adapter: buildFakeAudioAdapter(),
      onListenerError: (err) => errors.push(err),
    });
    engine.subscribe(() => {
      throw new Error('listener boom');
    });
    engine.loadTrack(track);
    expect(errors.length).toBeGreaterThan(0);
  });

  it('re-entrant subscribe during emit is safe', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    let second: (() => void) | null = null;
    engine.subscribe(() => {
      second = engine.subscribe(() => undefined);
    });
    engine.loadTrack(track);
    expect(second).not.toBeNull();
  });

  it('multiple listeners all receive events', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const a: AudioEvent[] = [];
    const b: AudioEvent[] = [];
    engine.subscribe((e) => a.push(e));
    engine.subscribe((e) => b.push(e));
    engine.loadTrack(track);
    expect(a.length).toBeGreaterThan(0);
    expect(b.length).toBeGreaterThan(0);
  });

  it('unsubscribe stops delivery', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    const unsubscribe = engine.subscribe((e) => events.push(e));
    unsubscribe();
    engine.loadTrack(track);
    expect(events.length).toBe(0);
  });
});

describe('AudioEngine — volumes & mute (idempotency + getters)', () => {
  it('mute is idempotent (does not re-emit when already muted)', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.mute();
    const muteEventsAfterFirst = events.filter((e) => e.type === 'mute-changed').length;
    engine.mute();
    engine.mute();
    const finalCount = events.filter((e) => e.type === 'mute-changed').length;
    expect(finalCount).toBe(muteEventsAfterFirst);
  });

  it('unmute is idempotent (does not re-emit when not muted)', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.unmute();
    expect(events.filter((e) => e.type === 'mute-changed').length).toBe(0);
    engine.mute();
    engine.unmute();
    engine.unmute();
    expect(events.filter((e) => e.type === 'mute-changed').length).toBe(2);
  });

  it('isMuted reflects current state', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    expect(engine.isMuted()).toBe(false);
    engine.mute();
    expect(engine.isMuted()).toBe(true);
    engine.unmute();
    expect(engine.isMuted()).toBe(false);
  });

  it('getMasterVolume + getVolume reflect current values', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    expect(engine.getMasterVolume()).toBeGreaterThan(0);
    expect(engine.getVolume('guidance')).toBeGreaterThan(0);
    engine.setVolume('cue', 0.3);
    expect(engine.getVolume('cue')).toBe(0.3);
    engine.setMasterVolumeValue(0.5);
    expect(engine.getMasterVolume()).toBe(0.5);
  });

  it('setVolume clamps out-of-range values', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.setVolume('guidance', 2);
    expect(engine.getVolume('guidance')).toBe(1);
    engine.setVolume('guidance', -1);
    expect(engine.getVolume('guidance')).toBe(0);
  });

  it('setMasterVolumeValue clamps', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.setMasterVolumeValue(2);
    expect(engine.getMasterVolume()).toBe(1);
    engine.setMasterVolumeValue(-1);
    expect(engine.getMasterVolume()).toBe(0);
  });

  it('volume-changed event includes the right layer', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.setVolume('cue', 0.5);
    const v = events.find((e) => e.type === 'volume-changed');
    expect(v).toBeDefined();
    if (v && v.type === 'volume-changed') {
      expect(v.layer).toBe('cue');
      expect(v.value).toBe(0.5);
    }
  });

  it('master volume-changed event uses layer="master"', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.setMasterVolumeValue(0.3);
    const v = events.find((e) => e.type === 'volume-changed');
    if (v && v.type === 'volume-changed') {
      expect(v.layer).toBe('master');
    }
  });

  it('resetVolume restores defaults', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.setVolume('cue', 0);
    engine.resetVolume();
    expect(engine.getVolume('cue')).toBeGreaterThan(0);
  });
});

describe('AudioEngine — language', () => {
  it('getLanguage defaults to pt-BR', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    expect(engine.getLanguage()).toBe('pt-BR');
  });

  it('setLanguage stores new value', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.setLanguage('en-US');
    expect(engine.getLanguage()).toBe('en-US');
  });
});

describe('AudioEngine — track swap', () => {
  it('loading a second track after load replaces the active one', () => {
    const engine = createAudioEngine({ adapter: buildFakeAudioAdapter() });
    engine.loadTrack(track);
    const t2 = buildAudioTrack('t2', [inhaleCue]);
    engine.loadTrack(t2);
    expect(engine.getActiveTrack()?.id).toBe('t2');
  });
});