/**
 * Curves — unit tests for all built-in curve functions.
 *
 * Tests verify:
 *   - Boundary conditions: f(0) == 0 and f(1) == 1.
 *   - Monotonicity (where applicable).
 *   - Symmetry (where applicable).
 *   - Known values at specific progress points.
 *   - No NaN/Infinity at boundaries.
 */

import {
  bezierCurve,
  cosineCurve,
  easeInCurve,
  easeInOutCurve,
  easeOutCurve,
  linearCurve,
  sineCurve,
  type CurveFn,
} from '@core/breath-engine';

const EPSILON = 1e-9;

const approx = (a: number, b: number, eps = EPSILON): boolean => Math.abs(a - b) < eps;

describe('curves — boundary conditions', () => {
  const allCurves: Array<[string, CurveFn]> = [
    ['linear', linearCurve],
    ['easeIn', easeInCurve],
    ['easeOut', easeOutCurve],
    ['easeInOut', easeInOutCurve],
    ['sine', sineCurve],
    ['cosine', cosineCurve],
    ['bezier', bezierCurve],
  ];

  test.each(allCurves)('%s: f(0) == 0', (_name, curve) => {
    expect(approx(curve(0), 0)).toBe(true);
  });

  test.each(allCurves)('%s: f(1) == 1', (_name, curve) => {
    expect(approx(curve(1), 1)).toBe(true);
  });

  test.each(allCurves)('%s: no NaN at boundaries', (_name, curve) => {
    expect(Number.isNaN(curve(0))).toBe(false);
    expect(Number.isNaN(curve(1))).toBe(false);
  });
});

describe('curves — monotonicity in [0, 1]', () => {
  const monotonicCurves: Array<[string, CurveFn]> = [
    ['linear', linearCurve],
    ['easeIn', easeInCurve],
    ['easeOut', easeOutCurve],
    ['easeInOut', easeInOutCurve],
    ['sine', sineCurve],
    ['cosine', cosineCurve],
    ['bezier', bezierCurve],
  ];

  test.each(monotonicCurves)('%s is monotonically non-decreasing', (_name, curve) => {
    let prev = curve(0);
    for (let i = 1; i <= 100; i += 1) {
      const x = i / 100;
      const y = curve(x);
      expect(y).toBeGreaterThanOrEqual(prev - EPSILON);
      prev = y;
    }
  });
});

describe('curves — specific values', () => {
  test('linear: f(0.5) == 0.5', () => {
    expect(linearCurve(0.5)).toBe(0.5);
  });

  test('easeIn (quadratic): f(0.5) == 0.25', () => {
    expect(approx(easeInCurve(0.5), 0.25)).toBe(true);
  });

  test('easeOut (quadratic): f(0.5) == 0.75', () => {
    expect(approx(easeOutCurve(0.5), 0.75)).toBe(true);
  });

  test('easeInOut: f(0.5) == 0.5', () => {
    expect(approx(easeInOutCurve(0.5), 0.5)).toBe(true);
  });

  test('easeInOut: f(0.25) == 0.125', () => {
    expect(approx(easeInOutCurve(0.25), 0.125)).toBe(true);
  });

  test('sine: f(0.5) ≈ 0.7071', () => {
    expect(approx(sineCurve(0.5), Math.sin(Math.PI / 4), 1e-6)).toBe(true);
  });

  test('cosine: f(0.5) == 0.5', () => {
    expect(approx(cosineCurve(0.5), 0.5)).toBe(true);
  });

  test('bezier: f(0.5) is close to 0.5', () => {
    // CSS ease cubic-bezier(0.42, 0, 0.58, 1) at x=0.5 should produce ~0.5
    const y = bezierCurve(0.5);
    expect(Math.abs(y - 0.5)).toBeLessThan(0.01);
  });
});

describe('curves — symmetry', () => {
  test('easeIn + easeOut sample points are complementary', () => {
    for (let i = 0; i <= 10; i += 1) {
      const x = i / 10;
      const ein = easeInCurve(x);
      const eout = easeOutCurve(x);
      expect(approx(ein + eout, x * 2, 1e-6)).toBe(true);
    }
  });

  test('easeInOut: f(x) + f(1-x) == 1', () => {
    for (let i = 0; i <= 10; i += 1) {
      const x = i / 10;
      const fx = easeInOutCurve(x);
      const f1x = easeInOutCurve(1 - x);
      expect(approx(fx + f1x, 1)).toBe(true);
    }
  });

  test('cosine: f(x) + f(1-x) == 1', () => {
    for (let i = 0; i <= 10; i += 1) {
      const x = i / 10;
      const fx = cosineCurve(x);
      const f1x = cosineCurve(1 - x);
      expect(approx(fx + f1x, 1, 1e-6)).toBe(true);
    }
  });
});

describe('curves — clamping behavior', () => {
  test('linear: extrapolates beyond [0,1]', () => {
    expect(linearCurve(1.5)).toBe(1.5);
    expect(linearCurve(-0.5)).toBe(-0.5);
  });

  test('easeIn: extrapolates beyond [0,1]', () => {
    expect(easeInCurve(2)).toBe(4);
    expect(easeInCurve(-1)).toBe(1);
  });
});

describe('curves — bezier precision', () => {
  test('bezier handles edge cases gracefully', () => {
    expect(approx(bezierCurve(0), 0)).toBe(true);
    expect(approx(bezierCurve(1), 1)).toBe(true);
    // Should not produce NaN at any interior point
    for (let i = 1; i < 100; i += 1) {
      const x = i / 100;
      expect(Number.isNaN(bezierCurve(x))).toBe(false);
      expect(Number.isFinite(bezierCurve(x))).toBe(true);
    }
  });

  test('bezier: f(0.1) < f(0.2) (monotonic)', () => {
    expect(bezierCurve(0.1)).toBeLessThan(bezierCurve(0.2));
  });
});