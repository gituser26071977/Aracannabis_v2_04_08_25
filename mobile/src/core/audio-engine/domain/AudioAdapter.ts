/**
 * AudioAdapter — the seam between the AudioEngine and any audio backend.
 *
 * The Engine owns state and logic; the Adapter owns the integration
 * with `expo-av`, `react-native-track-player`, the browser's Web
 * Audio API, or any other backend. Sprint 10 ships only the
 * `InMemoryAudioAdapter` (mock); real backends land in future
 * sprints.
 *
 * Contract:
 *   - All methods return Promises; errors come back as `Err` results
 *     rather than thrown exceptions, so the Engine can route them
 *     into the `'errored'` state explicitly.
 *   - Methods must be idempotent within a single state (e.g. calling
 *     `pause` twice is not an error).
 *   - `dispose` is terminal — subsequent calls are no-ops.
 */

import type { Result } from '@araflow/shared-contracts';
import { EngineError } from '@araflow/shared-contracts';

import type { AudioClip } from './AudioClip';
import type { AudioLayer } from './AudioLayer';

export type AudioAdapterError = EngineError;

export interface AudioAdapter {
  readonly id: string;
  load(clip: AudioClip): Promise<Result<void, AudioAdapterError>>;
  play(layer: AudioLayer, clipId: string): Promise<Result<void, AudioAdapterError>>;
  pause(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  resume(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  stop(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  setLayerVolume(layer: AudioLayer, value: number): Promise<Result<void, AudioAdapterError>>;
  setMasterVolume(value: number): Promise<Result<void, AudioAdapterError>>;
  dispose(): Promise<Result<void, AudioAdapterError>>;
}

export const isAudioAdapter = (v: unknown): v is AudioAdapter => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const a = v as Partial<AudioAdapter>;
  return (
    typeof a.id === 'string' &&
    typeof a.load === 'function' &&
    typeof a.play === 'function' &&
    typeof a.pause === 'function' &&
    typeof a.resume === 'function' &&
    typeof a.stop === 'function' &&
    typeof a.setLayerVolume === 'function' &&
    typeof a.setMasterVolume === 'function' &&
    typeof a.dispose === 'function'
  );
};