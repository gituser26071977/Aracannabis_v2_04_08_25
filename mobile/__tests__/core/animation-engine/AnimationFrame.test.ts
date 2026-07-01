/**
 * Tests for AnimationFrame and AnimationPhase domain types.
 */

import {
  ACTIVE_ANIMATION_PHASES,
  ANIMATION_PHASES,
  TERMINAL_ANIMATION_PHASES,
  isActiveAnimationPhase,
  isAnimationFrame,
  isAnimationPhase,
  isTerminalAnimationPhase,
  labelForPhase,
} from '@core/animation-engine';
import type { AnimationFrame } from '@core/animation-engine';

describe('AnimationPhase', () => {
  it('isAnimationPhase accepts valid phases', () => {
    for (const p of ANIMATION_PHASES) {
      expect(isAnimationPhase(p)).toBe(true);
    }
  });

  it('isAnimationPhase rejects invalid phases', () => {
    expect(isAnimationPhase('running')).toBe(false);
    expect(isAnimationPhase('')).toBe(false);
    expect(isAnimationPhase(null)).toBe(false);
  });

  it('labelForPhase returns a non-empty label for every phase', () => {
    for (const p of ANIMATION_PHASES) {
      expect(labelForPhase(p).length).toBeGreaterThan(0);
    }
  });

  it('isActiveAnimationPhase covers all but completed', () => {
    for (const p of ANIMATION_PHASES) {
      if (p === 'completed') {
        expect(isActiveAnimationPhase(p)).toBe(false);
      } else {
        expect(isActiveAnimationPhase(p)).toBe(true);
      }
    }
  });

  it('isTerminalAnimationPhase is true only for completed', () => {
    for (const p of ANIMATION_PHASES) {
      expect(isTerminalAnimationPhase(p)).toBe(p === 'completed');
    }
  });

  it('ACTIVE_ANIMATION_PHASES excludes completed', () => {
    expect(ACTIVE_ANIMATION_PHASES).not.toContain('completed');
  });

  it('TERMINAL_ANIMATION_PHASES contains only completed', () => {
    expect(TERMINAL_ANIMATION_PHASES).toEqual(['completed']);
  });
});

describe('AnimationFrame — type guard', () => {
  const validFrame: AnimationFrame = {
    timestamp: 0,
    phase: 'idle',
    normalizedProgress: 0,
    radius: 0.2,
    opacity: 0.4,
    scale: 1,
    easingCurve: 'easeInOut',
    breathingDepth: 0,
    label: 'Ready',
    remainingTime: 0,
  };

  it('accepts a valid frame', () => {
    expect(isAnimationFrame(validFrame)).toBe(true);
  });

  it('rejects null and non-objects', () => {
    expect(isAnimationFrame(null)).toBe(false);
    expect(isAnimationFrame(123)).toBe(false);
  });

  it('rejects frames with wrong field types', () => {
    const broken = { ...validFrame, timestamp: '0' };
    expect(isAnimationFrame(broken)).toBe(false);
  });

  it('rejects frames with non-string phase', () => {
    const broken = { ...validFrame, phase: 42 };
    expect(isAnimationFrame(broken)).toBe(false);
  });

  it('rejects frames with non-string easingCurve', () => {
    const broken = { ...validFrame, easingCurve: 7 };
    expect(isAnimationFrame(broken)).toBe(false);
  });
});
