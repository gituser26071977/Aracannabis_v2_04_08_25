/**
 * RuntimeEventStream — tagged-union event dispatcher.
 *
 * Mirrors `createEventDispatcher` from `@core/timer-engine`:
 * - listeners are stored in a Set
 * - emit() snapshots the Set to allow re-entrant subscribe/unsubscribe
 * - listener exceptions are caught and routed to `onListenerError`
 *   so a throwing listener does NOT break emission to other listeners
 *
 * Used by RuntimeEngine to fan-out the unified `RuntimeEvent` stream
 * to all subscribers. Internal engine subscriptions also go through
 * this stream so a single `subscribe()` call observes everything.
 */

import type {
  RuntimeEvent,
  RuntimeEventListener,
  RuntimeUnsubscribe,
} from '../domain/RuntimeEvent';

export interface RuntimeEventStream {
  subscribe(listener: RuntimeEventListener): RuntimeUnsubscribe;
  emit(event: RuntimeEvent): void;
  listenerCount(): number;
  clear(): void;
}

export const createRuntimeEventStream = (
  onListenerError?: (error: unknown, listener: RuntimeEventListener) => void,
): RuntimeEventStream => {
  const listeners = new Set<RuntimeEventListener>();

  const subscribe = (listener: RuntimeEventListener): RuntimeUnsubscribe => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  };

  const emit = (event: RuntimeEvent): void => {
    // Snapshot to allow re-entrant subscribe/unsubscribe during emit.
    const snapshot = [...listeners];
    for (const listener of snapshot) {
      try {
        listener(event);
      } catch (error) {
        if (onListenerError !== undefined) {
          onListenerError(error, listener);
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
