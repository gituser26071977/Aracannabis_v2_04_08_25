/**
 * Tests for the pure frame-computation utility.
 */

import {
  DEFAULT_ANIMATION_CONFIG,
  buildIdleFrame,
  computeAnimationFrame,
} from '@core/animation-engine';
import type { AnimationConfig } from '@core/animation-engine';

describe('computeAnimationFrame — phase interpolation', () => {
  const baseConfig = DEFAULT_ANIMATION_CONFIG;

  it('idle frame uses idleRadius and idleOpacity', () => {
    const frame = computeAnimationFrame({
      phase: 'idle',
      normalizedProgress: 0,
      hold: 'none',
      config: baseConfig,
      timestamp: 100,
      remainingTime: 0,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.idleRadius, 5);
    expect(frame.opacity).toBeCloseTo(baseConfig.idleOpacity, 5);
    expect(frame.label).toBe('Ready');
  });

  it('inhale at progress=0 is at trough', () => {
    const frame = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 1000,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.troughRadius, 5);
    expect(frame.breathingDepth).toBeCloseTo(0, 5);
    expect(frame.label).toBe('Breathe in');
  });

  it('inhale at progress=1 is at peak', () => {
    const frame = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 1,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.peakRadius, 5);
    expect(frame.breathingDepth).toBeCloseTo(1, 5);
  });

  it('exhale at progress=1 is back at trough', () => {
    const frame = computeAnimationFrame({
      phase: 'exhale',
      normalizedProgress: 1,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.troughRadius, 5);
    expect(frame.breathingDepth).toBeCloseTo(0, 5);
  });

  it('hold at peak holds the peak radius', () => {
    const frame = computeAnimationFrame({
      phase: 'hold',
      normalizedProgress: 0.5,
      hold: 'peak',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.peakRadius, 5);
    expect(frame.breathingDepth).toBeCloseTo(1, 5);
  });

  it('hold at trough holds the trough radius', () => {
    const frame = computeAnimationFrame({
      phase: 'hold',
      normalizedProgress: 0.5,
      hold: 'trough',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.radius).toBeCloseTo(baseConfig.troughRadius, 5);
    expect(frame.breathingDepth).toBeCloseTo(0, 5);
  });

  it('completed frame uses completedOpacity', () => {
    const frame = computeAnimationFrame({
      phase: 'completed',
      normalizedProgress: 1,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.opacity).toBeCloseTo(baseConfig.completedOpacity, 5);
    expect(frame.label).toBe('Complete');
  });

  it('preparing frame ramps opacity from idle to active', () => {
    const start = computeAnimationFrame({
      phase: 'preparing',
      normalizedProgress: 0,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    const end = computeAnimationFrame({
      phase: 'preparing',
      normalizedProgress: 1,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(start.opacity).toBeCloseTo(baseConfig.idleOpacity, 5);
    expect(end.opacity).toBeCloseTo(baseConfig.activeOpacity, 5);
  });
});

describe('computeAnimationFrame — easing', () => {
  const baseConfig = DEFAULT_ANIMATION_CONFIG;

  it('respects the configured easing curve', () => {
    const config: AnimationConfig = { ...baseConfig, easingCurve: 'linear' };
    const frame = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0.5,
      hold: 'none',
      config,
      timestamp: 0,
      remainingTime: 0,
    });
    // linear: eased progress = 0.5
    expect(frame.normalizedProgress).toBeCloseTo(0.5, 5);
    expect(frame.radius).toBeCloseTo(
      baseConfig.troughRadius + (baseConfig.peakRadius - baseConfig.troughRadius) * 0.5,
      5,
    );
  });

  it('produces different results with easeInOut vs linear at p=0.25', () => {
    // Both linear and easeInOut pass through (0.5, 0.5), so the symmetric
    // midpoint is the worst possible place to distinguish them. Pick 0.25
    // where easeInOut is materially below linear.
    const linear = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0.25,
      hold: 'none',
      config: { ...baseConfig, easingCurve: 'linear' },
      timestamp: 0,
      remainingTime: 0,
    });
    const easeInOut = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0.25,
      hold: 'none',
      config: { ...baseConfig, easingCurve: 'easeInOut' },
      timestamp: 0,
      remainingTime: 0,
    });
    expect(easeInOut.radius).toBeLessThan(linear.radius);
  });
});

describe('computeAnimationFrame — invariants', () => {
  const baseConfig = DEFAULT_ANIMATION_CONFIG;

  it('clamps normalizedProgress to [0, 1]', () => {
    const below = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: -0.5,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    const above = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 1.5,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(below.normalizedProgress).toBeGreaterThanOrEqual(0);
    expect(above.normalizedProgress).toBeLessThanOrEqual(1);
  });

  it('clamps radius to [0, 1]', () => {
    const frame = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0.5,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(frame.radius).toBeGreaterThanOrEqual(0);
    expect(frame.radius).toBeLessThanOrEqual(1);
  });

  it('returns a frozen object', () => {
    const frame = computeAnimationFrame({
      phase: 'idle',
      normalizedProgress: 0,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: 0,
    });
    expect(Object.isFrozen(frame)).toBe(true);
  });

  it('does not clamp negative remainingTime below 0', () => {
    const frame = computeAnimationFrame({
      phase: 'inhale',
      normalizedProgress: 0,
      hold: 'none',
      config: baseConfig,
      timestamp: 0,
      remainingTime: -100,
    });
    expect(frame.remainingTime).toBe(0);
  });
});

describe('buildIdleFrame', () => {
  it('produces an idle frame with timestamp=0 by default', () => {
    const frame = buildIdleFrame(DEFAULT_ANIMATION_CONFIG, 42);
    expect(frame.phase).toBe('idle');
    expect(frame.timestamp).toBe(42);
  });
});
