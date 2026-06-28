/**
 * EaseIn curve (quadratic): y = x^2.
 *
 * Começa devagar e acelera. Para inalação, isso modela a resistência
 * inicial dos pulmões; para exalação, modela retenção antes de soltar.
 */

import type { CurveFn } from '../Curve';

export const easeInCurve: CurveFn = (progress: number): number => {
  return progress * progress;
};