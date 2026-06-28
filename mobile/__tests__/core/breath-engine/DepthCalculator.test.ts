/**
 * DepthCalculator — unit tests for depth computation.
 */

import { computeDepth, linearCurve, easeInOutCurve } from '@core/breath-engine';

describe('DepthCalculator — null phase', () => {
  test('returns 0 for null phase (prep or completed)', () => {
    expect(computeDepth(null, 0, linearCurve)).toBe(0);
    expect(computeDepth(null, 0.5, linearCurve)).toBe(0);
    expect(computeDepth(null, 1, linearCurve)).toBe(0);
  });
});

describe('DepthCalculator — inhaling', () => {
  test('returns curve(progress) when inhaling', () => {
    expect(computeDepth('inhaling', 0, linearCurve)).toBe(0);
    expect(computeDepth('inhaling', 0.5, linearCurve)).toBe(0.5);
    expect(computeDepth('inhaling', 1, linearCurve)).toBe(1);
  });

  test('inhaling uses curve correctly', () => {
    expect(computeDepth('inhaling', 0.5, easeInOutCurve)).toBe(0.5);
  });
});

describe('DepthCalculator — holdAfterInhale', () => {
  test('returns 1 regardless of progress', () => {
    expect(computeDepth('holdAfterInhale', 0, linearCurve)).toBe(1);
    expect(computeDepth('holdAfterInhale', 0.5, linearCurve)).toBe(1);
    expect(computeDepth('holdAfterInhale', 1, linearCurve)).toBe(1);
  });
});

describe('DepthCalculator — exhaling', () => {
  test('returns 1 - curve(progress) when exhaling', () => {
    expect(computeDepth('exhaling', 0, linearCurve)).toBe(1);
    expect(computeDepth('exhaling', 0.5, linearCurve)).toBe(0.5);
    expect(computeDepth('exhaling', 1, linearCurve)).toBe(0);
  });

  test('exhaling mirrors inhaling', () => {
    expect(computeDepth('exhaling', 0, linearCurve)).toBe(1);
    expect(computeDepth('exhaling', 1, linearCurve)).toBe(0);
  });
});

describe('DepthCalculator — holdAfterExhale', () => {
  test('returns 0 regardless of progress', () => {
    expect(computeDepth('holdAfterExhale', 0, linearCurve)).toBe(0);
    expect(computeDepth('holdAfterExhale', 0.5, linearCurve)).toBe(0);
    expect(computeDepth('holdAfterExhale', 1, linearCurve)).toBe(0);
  });
});

describe('DepthCalculator — progress clamping', () => {
  test('clamps progress > 1 to 1', () => {
    expect(computeDepth('inhaling', 1.5, linearCurve)).toBe(1);
    expect(computeDepth('exhaling', 1.5, linearCurve)).toBe(0);
  });

  test('clamps progress < 0 to 0', () => {
    expect(computeDepth('inhaling', -0.5, linearCurve)).toBe(0);
    expect(computeDepth('exhaling', -0.5, linearCurve)).toBe(1);
  });
});

describe('DepthCalculator — full cycle integration', () => {
  test('inhale → hold → exhale → hold covers full depth range', () => {
    expect(computeDepth('inhaling', 1, linearCurve)).toBe(1);
    expect(computeDepth('holdAfterInhale', 0.5, linearCurve)).toBe(1);
    expect(computeDepth('exhaling', 0, linearCurve)).toBe(1);
    expect(computeDepth('exhaling', 1, linearCurve)).toBe(0);
    expect(computeDepth('holdAfterExhale', 0.5, linearCurve)).toBe(0);
  });
});