/**
 * AudioEvent — tagged-union event emitted by the AudioEngine.
 *
 * The Engine emits one of 11 event types. Every event carries the
 * `monotonicMs` timestamp copied from the source Runtime event (or
 * `0` for engine-initiated events like volume-changed when not bound
 * to a Runtime). Consumers subscribe via `subscribe(listener)`.
 */

import type { AudioLayer } from './AudioLayer';
import type { AudioLanguage } from './AudioLanguage';

export type AudioEvent =
  | {
      readonly type: 'audio-started';
      readonly trackId: string;
      readonly layer: AudioLayer | null;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'audio-paused';
      readonly atElapsedMs: number;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'audio-resumed';
      readonly pausedForMs: number;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'audio-stopped';
      readonly reason: 'completed' | 'cancelled' | 'errored';
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'track-loaded';
      readonly trackId: string;
      readonly layer: AudioLayer;
      readonly clipCount: number;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'cue-played';
      readonly cueId: string;
      readonly layer: AudioLayer;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'guidance-played';
      readonly text: string;
      readonly language: AudioLanguage;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'ambient-started';
      readonly trackId: string;
      readonly clipId: string;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'music-started';
      readonly trackId: string;
      readonly clipId: string;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'volume-changed';
      readonly layer: AudioLayer | 'master';
      readonly value: number;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'mute-changed';
      readonly muted: boolean;
      readonly monotonicMs: number;
    };

export type AudioEventType = AudioEvent['type'];

export const AUDIO_EVENT_TYPES: readonly AudioEventType[] = [
  'audio-started',
  'audio-paused',
  'audio-resumed',
  'audio-stopped',
  'track-loaded',
  'cue-played',
  'guidance-played',
  'ambient-started',
  'music-started',
  'volume-changed',
  'mute-changed',
] as const;

export type AudioEventListener = (event: AudioEvent) => void;

export type AudioUnsubscribe = () => void;

export const isAudioEvent = (v: unknown): v is AudioEvent => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const e = v as { type?: unknown };
  return typeof e.type === 'string' && (AUDIO_EVENT_TYPES as readonly string[]).includes(e.type);
};