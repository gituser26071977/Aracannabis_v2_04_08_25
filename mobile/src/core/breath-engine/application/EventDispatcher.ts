/**
 * EventDispatcher — sistema de pub/sub type-safe para BreathEvent.
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
 * Mesmo padrão do Timer Engine, mas typed para BreathEvent para
 * manter baixo acoplamento entre os dois engines.
 *
 * Uso:
 *   const dispatcher = createBreathEventDispatcher();
 *   const unsubscribe = dispatcher.subscribe((event) => { ... });
 *   dispatcher.emit({ type: 'phaseChanged', ... });
 *   unsubscribe();
 */

import type { BreathEvent, BreathListener, BreathUnsubscribe } from '../domain';

export interface BreathEventDispatcher {
  subscribe(listener: BreathListener): BreathUnsubscribe;
  emit(event: BreathEvent): void;
  listenerCount(): number;
  clear(): void;
}

export const createBreathEventDispatcher = (
  onListenerError?: (error: unknown, listener: BreathListener) => void,
): BreathEventDispatcher => {
  const listeners = new Set<BreathListener>();

  const subscribe = (listener: BreathListener): BreathUnsubscribe => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  };

  const emit = (event: BreathEvent): void => {
    // Snapshot to make re-entrant operations safe.
    const snapshot = Array.from(listeners);
    for (const listener of snapshot) {
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