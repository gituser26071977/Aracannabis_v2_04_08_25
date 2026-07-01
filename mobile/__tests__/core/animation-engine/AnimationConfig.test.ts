/**
 * Tests for AnimationConfig — default values, validation, clamping.
 */

import { DEFAULT_ANIMATION_CONFIG, clamp, validateAnimationConfig } from '@core/animation-engine';
import type { AnimationConfig } from '@core/animation-engine';

describe('AnimationConfig — default', () => {
  it('uses easeInOut as the default easing curve', () => {
    expect(DEFAULT_ANIMATION_CONFIG.easingCurve).toBe('easeInOut');
  });

  it('uses 0.2 idle radius and 1.0 peak radius', () => {
    expect(DEFAULT_ANIMATION_CONFIG.idleRadius).toBe(0.2);
    expect(DEFAULT_ANIMATION_CONFIG.peakRadius).toBe(1.0);
  });

  it('is frozen', () => {
    expect(Object.isFrozen(DEFAULT_ANIMATION_CONFIG)).toBe(true);
  });
});

describe('AnimationConfig — validate', () => {
  it('accepts the default config', () => {
    expect(() => validateAnimationConfig(DEFAULT_ANIMATION_CONFIG)).not.toThrow();
  });

  it('rejects out-of-range values', () => {
    const bad: AnimationConfig = { ...DEFAULT_ANIMATION_CONFIG, idleRadius: 1.5 };
    expect(() => validateAnimationConfig(bad)).toThrow(/idleRadius/);
  });

  it('rejects NaN', () => {
    const bad: AnimationConfig = { ...DEFAULT_ANIMATION_CONFIG, peakRadius: Number.NaN };
    expect(() => validateAnimationConfig(bad)).toThrow(/peakRadius/);
  });
});

describe('clamp', () => {
  it('clamps below min', () => {
    expect(clamp(-1, 0, 1)).toBe(0);
  });
  it('clamps above max', () => {
    expect(clamp(2, 0, 1)).toBe(1);
  });
  it('returns value when in range', () => {
    expect(clamp(0.5, 0, 1)).toBe(0.5);
  });
});
