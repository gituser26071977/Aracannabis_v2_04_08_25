/**
 * EaseOut curve (quadratic): y = 1 - (1 - x)^2.
 *
 * Começa rápido e desacelera. Para inalação, modela expansão rápida
 * seguida de slowdown ao encher; para exalação, modela esvaziamento
 * rápido seguido de pausa natural.
 */

import type { CurveFn } from '../Curve';

export const easeOutCurve: CurveFn = (progress: number): number => {
  const inv = 1 - progress;
  return 1 - inv * inv;
};