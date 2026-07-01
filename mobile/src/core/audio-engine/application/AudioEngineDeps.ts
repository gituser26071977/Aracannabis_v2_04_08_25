/**
 * AudioEngineDeps — constructor options for the AudioEngine.
 *
 * The Engine is a pure orchestrator: it does not own timers, audio
 * sources, or network. All interaction with audio hardware is
 * delegated to the `AudioAdapter`. The optional `runtime` is the
 * only clock the Engine trusts — events from the Runtime drive all
 * playback decisions.
 */

import type { RuntimeEngine } from '@core/runtime';

import type { AudioAdapter } from '../domain/AudioAdapter';
import type { AudioEventListener } from '../domain/AudioEvent';

export interface AudioEngineDeps {
  /** Backend that actually plays/stops audio. Required. */
  readonly adapter: AudioAdapter;
  /**
   * Optional Runtime — when supplied, the Engine subscribes once at
   * construction and reacts to Runtime events (phase-changed,
   * started/paused/resumed/stopped, completed, cancelled).
   */
  readonly runtime?: RuntimeEngine;
  /** Optional sink for listener exceptions. Defaults to no-op. */
  readonly onListenerError?: (error: unknown, listener: AudioEventListener) => void;
  /** Engine identifier (for logging and the event stream). */
  readonly engineId?: string;
}

export const DEFAULT_AUDIO_ENGINE_ID = 'araflow-audio-v1' as const;