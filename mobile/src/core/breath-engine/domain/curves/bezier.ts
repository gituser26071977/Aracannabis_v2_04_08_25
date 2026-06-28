/**
 * Bezier curve (cubic): CSS ease cubic-bezier approximation.
 *
 * Control points: (0.42, 0.0, 0.58, 1.0) — same as CSS `ease` keyword.
 * Provides smooth S-curve interpolation suitable for breathing visuals.
 *
 * Uses Newton-Raphson iteration to solve the parametric cubic Bezier
 * equation for x, then computes y from the cubic Bezier formula.
 */

import type { CurveFn } from '../Curve';

const P1X = 0.42;
const P1Y = 0.0;
const P2X = 0.58;
const P2Y = 1.0;

const cubicBezier = (t: number): number => {
  const u = 1 - t;
  return 3 * u * u * t * P1X + 3 * u * t * t * P2X + t * t * t;
};

const cubicBezierDerivative = (t: number): number => {
  const u = 1 - t;
  return 3 * u * u * P1X + 6 * u * t * (P2X - P1X) + 3 * t * t * (1 - P2X);
};

const cubicBezierY = (t: number): number => {
  const u = 1 - t;
  return 3 * u * u * t * P1Y + 3 * u * t * t * P2Y + t * t * t;
};

const NEWTON_ITERATIONS = 8;
const NEWTON_TOLERANCE = 1e-5;
const SUBDIVISION_PRECISION = 1e-7;
const SUBDIVISION_MAX_ITER = 20;

const A_X = 1 - 3 * P2X + 3 * P1X;
const B_X = 3 * P2X - 6 * P1X;
const C_X = 3 * P1X;

const sampleX = (t: number): number => ((A_X * t + B_X) * t + C_X) * t;
const sampleXDerivative = (t: number): number => (3 * A_X * t + 2 * B_X) * t + C_X;

/**
 * Find parameter t for given x using Newton-Raphson with subdivision fallback.
 */
const solveForT = (x: number): number => {
  let t = x;
  for (let i = 0; i < NEWTON_ITERATIONS; i += 1) {
    const residual = sampleX(t) - x;
    if (Math.abs(residual) < NEWTON_TOLERANCE) {
      return t;
    }
    const derivative = sampleXDerivative(t);
    if (Math.abs(derivative) < 1e-10) {
      break;
    }
    t -= residual / derivative;
  }

  // Fallback: bisection.
  let lo = 0;
  let hi = 1;
  t = x;
  for (let i = 0; i < SUBDIVISION_MAX_ITER; i += 1) {
    const xEst = sampleX(t);
    const residual = xEst - x;
    if (Math.abs(residual) < SUBDIVISION_PRECISION) {
      return t;
    }
    if (residual > 0) {
      hi = t;
    } else {
      lo = t;
    }
    t = (hi + lo) / 2;
  }
  return t;
};

export const bezierCurve: CurveFn = (progress: number): number => {
  if (progress <= 0) return 0;
  if (progress >= 1) return 1;
  const t = solveForT(progress);
  return cubicBezierY(t);
};

// Silence unused warnings for module-level helpers used only via closures.
void cubicBezier;
void cubicBezierDerivative;