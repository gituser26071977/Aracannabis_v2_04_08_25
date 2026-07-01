/**
 * Tests for AnimationEvent tagged union — type guard, event-type list.
 */

import { ANIMATION_EVENT_TYPES, isAnimationEvent } from '@core/animation-engine';
import type { AnimationEvent } from '@core/animation-engine';

describe('AnimationEvent — type guard', () => {
  const makePaused = (): AnimationEvent => ({
    type: 'animation-engine-paused',
    monotonicMs: 0,
    frozenFrame: {
      timestamp: 0,
      phase: 'idle',
      normalizedProgress: 0,
      radius: 0,
      opacity: 0,
      scale: 0,
      easingCurve: 'linear',
      breathingDepth: 0,
      label: 'Ready',
      remainingTime: 0,
    },
  });
  const makeGeneric = (t: AnimationEvent['type']): AnimationEvent =>
    ({ type: t, monotonicMs: 0 }) as AnimationEvent;

  it('accepts every documented event type', () => {
    for (const t of ANIMATION_EVENT_TYPES) {
      const event = t === 'animation-engine-paused' ? makePaused() : makeGeneric(t);
      expect(isAnimationEvent(event)).toBe(true);
    }
  });

  it('rejects non-objects', () => {
    expect(isAnimationEvent(null)).toBe(false);
    expect(isAnimationEvent(123)).toBe(false);
    expect(isAnimationEvent('animation-frame')).toBe(false);
  });

  it('rejects unknown event types', () => {
    expect(isAnimationEvent({ type: 'animation-bogus', monotonicMs: 0 })).toBe(false);
  });

  it('rejects events missing type field', () => {
    expect(isAnimationEvent({ monotonicMs: 0 })).toBe(false);
  });
});

describe('ANIMATION_EVENT_TYPES', () => {
  it('contains every tagged-union variant', () => {
    expect(ANIMATION_EVENT_TYPES).toEqual([
      'animation-frame',
      'animation-engine-started',
      'animation-engine-paused',
      'animation-engine-resumed',
      'animation-engine-disposed',
    ]);
  });
});
