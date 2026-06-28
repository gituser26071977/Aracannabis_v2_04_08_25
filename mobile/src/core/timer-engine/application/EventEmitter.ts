/**
 * EventEmitter — sistema de pub/sub type-safe.
 *
 * Características:
 *   - Síncrono: dispatch ocorre imediatamente após emit.
 *   - Re-entrante seguro: subscribe/unsubscribe durante dispatch não
 *     afeta a iteração atual (snapshot da lista é feito no início).
 *   - Erros em listeners são capturados e logados, mas não
 *     interrompem o dispatch para outros listeners.
 *   - Listener type `void` (fire-and-forget) — erros não são
 *     propagados ao produtor do evento.
 *
 * Uso:
 *   const emitter = new EventEmitter<MyEvent>();
 *   const unsubscribe = emitter.subscribe((event) => { ... });
 *   emitter.emit({ type: 'foo' });
 *   unsubscribe();
 */

import type { TimerListener, Unsubscribe } from '../domain/Listener';

export interface EventDispatcher {
  subscribe(listener: TimerListener): Unsubscribe;
  emit(event: Parameters<TimerListener>[0]): void;
  listenerCount(): number;
  clear(): void;
}

export const createEventDispatcher = (
  onListenerError?: (error: unknown, listener: TimerListener) => void,
): EventDispatcher => {
  const listeners = new Set<TimerListener>();

  const subscribe = (listener: TimerListener): Unsubscribe => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  };

  const emit = (event: Parameters<TimerListener>[0]): void => {
    // Snapshot to make re-entrant operations safe.
    const snapshot = Array.from(listeners);
    for (const listener of snapshot) {
      // If a listener was removed during iteration, Set.has returns false;
      // we still call it because the snapshot is authoritative.
      try {
        listener(event);
      } catch (error: unknown) {
        if (onListenerError !== undefined) {
          onListenerError(error, listener);
        }
        // Swallow: errors in listeners never break the engine.
      }
    }
  };

  const listenerCount = (): number => listeners.size;

  const clear = (): void => {
    listeners.clear();
  };

  return { subscribe, emit, listenerCount, clear };
};
