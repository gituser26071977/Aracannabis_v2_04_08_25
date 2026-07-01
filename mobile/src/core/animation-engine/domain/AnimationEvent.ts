/**
 * AnimationEvent — tagged-union of events emitted by the Animation
 * Engine. Consumers subscribe via `animationEngine.subscribe(listener)`.
 */

import type { AnimationFrame } from './AnimationFrame';

export type AnimationEvent =
  | {
      readonly type: 'animation-frame';
      readonly monotonicMs: number;
      readonly frame: AnimationFrame;
    }
  | {
      readonly type: 'animation-engine-started';
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'animation-engine-paused';
      readonly monotonicMs: number;
      readonly frozenFrame: AnimationFrame;
    }
  | {
      readonly type: 'animation-engine-resumed';
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'animation-engine-disposed';
      readonly monotonicMs: number;
    };

export type AnimationEventListener = (event: AnimationEvent) => void;
export type AnimationUnsubscribe = () => void;

export const ANIMATION_EVENT_TYPES: readonly AnimationEvent['type'][] = [
  'animation-frame',
  'animation-engine-started',
  'animation-engine-paused',
  'animation-engine-resumed',
  'animation-engine-disposed',
] as const;

export const isAnimationEvent = (v: unknown): v is AnimationEvent => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const t = (v as { type?: unknown }).type;
  return typeof t === 'string' && (ANIMATION_EVENT_TYPES as readonly string[]).includes(t);
};
