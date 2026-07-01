/**
 * AnimationEventStream — tagged-union dispatcher for AnimationEngine.
 *
 * Mirrors the pattern from Runtime/Orchestrator: listeners are
 * isolated so a throwing listener does not break emission to others.
 * Re-entrant subscribe/unsubscribe during emit is safe — the
 * listener snapshot is taken once at emit time.
 */

import type {
  AnimationEvent,
  AnimationEventListener,
  AnimationUnsubscribe,
} from '../domain/AnimationEvent';

export interface AnimationEventStream {
  subscribe(listener: AnimationEventListener): AnimationUnsubscribe;
  emit(event: AnimationEvent, onError?: (err: unknown) => void): void;
  clear(): void;
  size(): number;
}

export const createAnimationEventStream = (): AnimationEventStream => {
  const listeners = new Set<AnimationEventListener>();

  return {
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    emit(event, onError) {
      const snapshot = Array.from(listeners);
      for (const listener of snapshot) {
        try {
          listener(event);
        } catch (err) {
          if (onError) {
            try {
              onError(err);
            } catch {
              // swallow sink errors
            }
          }
        }
      }
    },
    clear() {
      listeners.clear();
    },
    size() {
      return listeners.size;
    },
  };
};
