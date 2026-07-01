/**
 * AudioEngine — the Audio Engine orchestrator.
 *
 * Owns:
 *   - The 7-state FSM (`AudioEngineState`).
 *   - The active `AudioTrack` reference.
 *   - The `AudioVolumeMap` (master + per-layer).
 *   - The active `AudioLanguage`.
 *   - The mute flag.
 *   - One subscription to the `Runtime` (if supplied).
 *   - The `AudioEventStream` for outgoing events.
 *
 * Owns nothing related to:
 *   - Time (no timers, no `Date.now()` — only Runtime-supplied
 *     `monotonicMs`).
 *   - Audio hardware (delegated to `AudioAdapter`).
 *   - UI / RN / React.
 *
 * The Engine reacts to Runtime events:
 *
 *   timer.started            → play()
 *   timer.paused             → pause()
 *   timer.resumed            → resume()
 *   timer.stopped            → stop()
 *   breath.phase-changed     → lookup phaseToCueId + adapter.play('cue', id)
 *   breath.breath-started    → adapter.play('ambient', ambientClip)
 *   breath.completed         → adapter.stop('ambient'), adapter.stop('music')
 *   breath.cancelled         → adapter.stop('ambient'), adapter.stop('music')
 *   breath.resumed-from-int. → adapter.resume() for each layer
 */

import type { Result } from '@araflow/shared-contracts';
import { EngineError, Err, Ok } from '@araflow/shared-contracts';
import type { RuntimeEvent, RuntimeUnsubscribe } from '@core/runtime';

import type { AudioAdapter } from '../domain/AudioAdapter';
import type { AudioClip } from '../domain/AudioClip';
import type {
  AudioEventListener,
  AudioUnsubscribe,
} from '../domain/AudioEvent';
import { AUDIO_EVENT_TYPES } from '../domain/AudioEvent';
import type { AudioLanguage } from '../domain/AudioLanguage';
import type { AudioLayer } from '../domain/AudioLayer';
import type { AudioTrack } from '../domain/AudioTrack';
import {
  type AudioEngineState,
  canAudioEngineTransition,
  isTerminalAudioEngineState,
} from '../domain/AudioEngineState';
import {
  type AudioVolumeMap,
  DEFAULT_AUDIO_VOLUME,
  buildAudioVolumeMap,
  setLayerVolume,
  setMasterVolume,
  volumeForLayer,
} from '../domain/AudioVolume';
import { DEFAULT_AUDIO_LANGUAGE } from '../domain/AudioLanguage';
import { findClipById } from '../domain/AudioTrack';
import { effectiveVolume } from '../util/volume-math';
import { phaseToCueEntry } from '../util/phase-to-cue';
import { createAudioEventStream, type AudioEventStream } from './AudioEventStream';
import type { AudioEngineDeps } from './AudioEngineDeps';
import { DEFAULT_AUDIO_ENGINE_ID } from './AudioEngineDeps';

export class AudioEngine {
  public readonly id: string;
  public readonly adapter: AudioAdapter;

  private readonly _runtime: AudioEngineDeps['runtime'];
  private readonly _stream: AudioEventStream;
  private readonly _unsubscribeRuntime: { current: RuntimeUnsubscribe | null };

  private _state: AudioEngineState = 'uninitialized';
  private _track: AudioTrack | null = null;
  private _volume: AudioVolumeMap = DEFAULT_AUDIO_VOLUME;
  private _language: AudioLanguage = DEFAULT_AUDIO_LANGUAGE;
  private _muted = false;
  private _pausedAtMs: number | null = null;

  public constructor(deps: AudioEngineDeps) {
    this.id = deps.engineId ?? DEFAULT_AUDIO_ENGINE_ID;
    this.adapter = deps.adapter;
    this._runtime = deps.runtime;
    this._stream = createAudioEventStream(deps.onListenerError);
    this._unsubscribeRuntime = { current: null };

    if (this._runtime !== undefined) {
      this._unsubscribeRuntime.current = this._runtime.subscribe(this._onRuntimeEvent);
    }
  }

  // ─── Public API ─────────────────────────────────────────────────

  public subscribe = (listener: AudioEventListener): AudioUnsubscribe => {
    if (isTerminalAudioEngineState(this._state)) {
      return (): void => undefined;
    }
    return this._stream.subscribe(listener);
  };

  public getState = (): AudioEngineState => this._state;

  public getActiveTrack = (): AudioTrack | null => this._track;

  public getLanguage = (): AudioLanguage => this._language;

  public setLanguage = (lang: AudioLanguage): void => {
    this._language = lang;
  };

  public getVolume = (layer: AudioLayer): number => volumeForLayer(this._volume, layer);

  public getMasterVolume = (): number => this._volume.master;

  public setVolume = (layer: AudioLayer, value: number): void => {
    const clamped = Math.max(0, Math.min(1, value));
    this._volume = setLayerVolume(this._volume, layer, clamped);
    this._stream.emit({
      type: 'volume-changed',
      layer,
      value: clamped,
      monotonicMs: 0,
    });
    void this.adapter.setLayerVolume(layer, effectiveVolume(this._volume.master, clamped, this._muted));
  };

  public setMasterVolumeValue = (value: number): void => {
    const clamped = Math.max(0, Math.min(1, value));
    this._volume = setMasterVolume(this._volume, clamped);
    this._stream.emit({
      type: 'volume-changed',
      layer: 'master',
      value: clamped,
      monotonicMs: 0,
    });
    void this.adapter.setMasterVolume(clamped);
  };

  public isMuted = (): boolean => this._muted;

  public mute = (): void => {
    if (this._muted) {
      return;
    }
    this._muted = true;
    this._stream.emit({ type: 'mute-changed', muted: true, monotonicMs: 0 });
  };

  public unmute = (): void => {
    if (!this._muted) {
      return;
    }
    this._muted = false;
    this._stream.emit({ type: 'mute-changed', muted: false, monotonicMs: 0 });
  };

  public loadTrack = (track: AudioTrack): Result<void, EngineError> => {
    if (!canAudioEngineTransition(this._state, 'loaded')) {
      return Err(
        new EngineError(
          `audio-engine: cannot load track in state '${this._state}'`,
          { code: 'audio_engine_invalid_state', severity: 'error' },
        ),
      );
    }
    if (track.clips.length === 0) {
      return Err(
        new EngineError('audio-engine: track has no clips', {
          code: 'audio_engine_empty_track',
          severity: 'error',
        }),
      );
    }
    const previousTrack = this._track;
    this._track = track;
    this._transition('loaded');
    this._stream.emit({
      type: 'track-loaded',
      trackId: track.id,
      layer: 'guidance',
      clipCount: track.clips.length,
      monotonicMs: 0,
    });
    // Stop layers from the previous track (if any).
    if (previousTrack !== null) {
      void this.adapter.stop('guidance');
      void this.adapter.stop('cue');
      void this.adapter.stop('ambient');
      void this.adapter.stop('music');
    }
    return Ok(undefined);
  };

  public play = (): Result<void, EngineError> => {
    if (!canAudioEngineTransition(this._state, 'playing')) {
      return Err(
        new EngineError(
          `audio-engine: cannot play in state '${this._state}'`,
          { code: 'audio_engine_invalid_state', severity: 'error' },
        ),
      );
    }
    const trackId = this._track?.id ?? '';
    this._transition('playing');
    this._pausedAtMs = null;
    this._stream.emit({
      type: 'audio-started',
      trackId,
      layer: null,
      monotonicMs: 0,
    });
    return Ok(undefined);
  };

  public pause = (): Result<void, EngineError> => {
    if (!canAudioEngineTransition(this._state, 'paused')) {
      return Err(
        new EngineError(
          `audio-engine: cannot pause in state '${this._state}'`,
          { code: 'audio_engine_invalid_state', severity: 'error' },
        ),
      );
    }
    this._pausedAtMs = 0;
    this._transition('paused');
    this._stream.emit({
      type: 'audio-paused',
      atElapsedMs: 0,
      monotonicMs: 0,
    });
    return Ok(undefined);
  };

  public resume = (): Result<void, EngineError> => {
    if (this._state !== 'paused') {
      return Err(
        new EngineError(
          `audio-engine: cannot resume in state '${this._state}'`,
          { code: 'audio_engine_invalid_state', severity: 'error' },
        ),
      );
    }
    const pausedForMs = this._pausedAtMs ?? 0;
    this._pausedAtMs = null;
    this._transition('playing');
    this._stream.emit({
      type: 'audio-resumed',
      pausedForMs,
      monotonicMs: 0,
    });
    return Ok(undefined);
  };

  public stop = (): Result<void, EngineError> => {
    if (!canAudioEngineTransition(this._state, 'stopped')) {
      return Err(
        new EngineError(
          `audio-engine: cannot stop in state '${this._state}'`,
          { code: 'audio_engine_invalid_state', severity: 'error' },
        ),
      );
    }
    this._transition('stopped');
    this._stream.emit({
      type: 'audio-stopped',
      reason: 'cancelled',
      monotonicMs: 0,
    });
    void this.adapter.stop('guidance');
    void this.adapter.stop('cue');
    void this.adapter.stop('ambient');
    void this.adapter.stop('music');
    return Ok(undefined);
  };

  public dispose = (): void => {
    if (isTerminalAudioEngineState(this._state)) {
      return;
    }
    if (canAudioEngineTransition(this._state, 'stopped')) {
      this._stream.emit({
        type: 'audio-stopped',
        reason: 'cancelled',
        monotonicMs: 0,
      });
    }
    if (this._unsubscribeRuntime.current !== null) {
      this._unsubscribeRuntime.current();
      this._unsubscribeRuntime.current = null;
    }
    this._stream.clear();
    this._track = null;
    this._transition('disposed');
    void this.adapter.dispose();
  };

  /** Reset volume to defaults — useful for tests and "reset" UX. */
  public resetVolume = (): void => {
    this._volume = buildAudioVolumeMap(this._volume.master);
  };

  // ─── Internal ───────────────────────────────────────────────────

  private _transition = (next: AudioEngineState): void => {
    this._state = next;
  };

  /**
   * Translate a RuntimeEvent into audio reactions. This is the ONLY
   * function that touches the adapter as a result of external stimuli.
   */
  private _onRuntimeEvent = (event: RuntimeEvent): void => {
    if (isTerminalAudioEngineState(this._state)) {
      return;
    }
    if (event.source === 'timer') {
      const t = event.payload;
      switch (t.type) {
        case 'started':
          this.play();
          return;
        case 'paused':
          this.pause();
          return;
        case 'resumed':
          this.resume();
          return;
        case 'stopped':
          this.stop();
          return;
        default:
          return;
      }
    }
    if (event.source === 'breath') {
      const b = event.payload;
      switch (b.type) {
        case 'phase-changed':
          this._handlePhaseChanged(b.currentPhase, b.monotonicMs);
          return;
        case 'breath-started':
          this._handleAmbientStart(b.monotonicMs);
          return;
        case 'completed':
          this._handleAmbientStop(b.monotonicMs);
          return;
        case 'cancelled':
          this._handleAmbientStop(b.monotonicMs);
          return;
        case 'resumed-from-interrupt':
          this._handleResumeFromInterrupt(b.monotonicMs);
          return;
        default:
          return;
      }
    }
  };

  private _handlePhaseChanged = (phase: string, monotonicMs: number): void => {
    // idle = no breath activity = no audible cue.
    if (phase === 'idle') {
      return;
    }
    const entry = phaseToCueEntry(
      phase as Parameters<typeof phaseToCueEntry>[0],
      this._language,
    );
    if (entry === null) {
      return;
    }
    void this.adapter.play('cue', entry.cueId);
    this._stream.emit({
      type: 'cue-played',
      cueId: entry.cueId,
      layer: 'cue',
      monotonicMs,
    });
    if (entry.guidanceText.length > 0) {
      void this.adapter.play('guidance', `guidance.${this._language}.${phase}`);
      this._stream.emit({
        type: 'guidance-played',
        text: entry.guidanceText,
        language: this._language,
        monotonicMs,
      });
    }
  };

  private _handleAmbientStart = (monotonicMs: number): void => {
    const track = this._track;
    if (track === null) {
      return;
    }
    const ambientId = track.layerDefaults?.ambient ?? 'ambient.rain-soft';
    const ambientClip: AudioClip | null = findClipById(track, ambientId);
    if (ambientClip !== null) {
      void this.adapter.play('ambient', ambientClip.id);
      this._stream.emit({
        type: 'ambient-started',
        trackId: track.id,
        clipId: ambientClip.id,
        monotonicMs,
      });
    }
    const musicId = track.layerDefaults?.music;
    if (musicId !== undefined) {
      const musicClip: AudioClip | null = findClipById(track, musicId);
      if (musicClip !== null) {
        void this.adapter.play('music', musicClip.id);
        this._stream.emit({
          type: 'music-started',
          trackId: track.id,
          clipId: musicClip.id,
          monotonicMs,
        });
      }
    }
  };

  private _handleAmbientStop = (monotonicMs: number): void => {
    void this.adapter.stop('ambient');
    void this.adapter.stop('music');
    if (canAudioEngineTransition(this._state, 'stopped')) {
      this._stream.emit({
        type: 'audio-stopped',
        reason: 'completed',
        monotonicMs,
      });
      this._transition('stopped');
    }
  };

  private _handleResumeFromInterrupt = (_monotonicMs: number): void => {
    void this.adapter.resume('guidance');
    void this.adapter.resume('cue');
    void this.adapter.resume('ambient');
    void this.adapter.resume('music');
  };

  // Re-export event types for tests / diagnostics.
  public static readonly eventTypes = AUDIO_EVENT_TYPES;
}