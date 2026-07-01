/**
 * AudioEventStream — typed event dispatcher for AudioEvents.
 *
 * Mirrors the proven pattern from
 * `mobile/src/core/runtime/application/RuntimeEventStream.ts`:
 *
 *   - Listeners stored in a Set
 *   - Snapshot at emit time (re-entrant subscribe/unsubscribe is safe)
 *   - try/catch around each listener invocation
 *   - errors routed to optional `onListenerError` sink
 *
 * The Engine owns one instance; `subscribe` returns the unsubscribe
 * closure.
 */

import type { AudioEvent, AudioEventListener, AudioUnsubscribe } from '../domain/AudioEvent';

export interface AudioEventStream {
  subscribe(listener: AudioEventListener): AudioUnsubscribe;
  emit(event: AudioEvent): void;
  listenerCount(): number;
  clear(): void;
}

export const createAudioEventStream = (
  onListenerError?: (error: unknown, listener: AudioEventListener) => void,
): AudioEventStream => {
  const listeners = new Set<AudioEventListener>();

  const subscribe = (listener: AudioEventListener): AudioUnsubscribe => {
    listeners.add(listener);
    return (): void => {
      listeners.delete(listener);
    };
  };

  const emit = (event: AudioEvent): void => {
    const snapshot = Array.from(listeners);
    for (const listener of snapshot) {
      try {
        listener(event);
      } catch (err) {
        if (onListenerError !== undefined) {
          onListenerError(err, listener);
        }
      }
    }
  };

  const listenerCount = (): number => listeners.size;

  const clear = (): void => {
    listeners.clear();
  };

  return { subscribe, emit, listenerCount, clear };
};