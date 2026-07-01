/**
 * OrchestratorEventStream — tagged-union event dispatcher.
 *
 * Mirrors `createRuntimeEventStream` from @core/runtime:
 *   - listeners stored in a Set
 *   - emit() snapshots the Set to allow re-entrant subscribe/unsubscribe
 *   - listener exceptions routed to `onListenerError` so a single
 *     throwing listener cannot break emission to others.
 */

import type {
  OrchestratorEvent,
  OrchestratorEventListener,
  OrchestratorUnsubscribe,
} from '../domain/OrchestratorEvent';

export interface OrchestratorEventStream {
  subscribe(listener: OrchestratorEventListener): OrchestratorUnsubscribe;
  emit(event: OrchestratorEvent): void;
  listenerCount(): number;
  clear(): void;
}

export const createOrchestratorEventStream = (
  onListenerError?: (error: unknown, listener: OrchestratorEventListener) => void,
): OrchestratorEventStream => {
  const listeners = new Set<OrchestratorEventListener>();

  const subscribe = (listener: OrchestratorEventListener): OrchestratorUnsubscribe => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  };

  const emit = (event: OrchestratorEvent): void => {
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
