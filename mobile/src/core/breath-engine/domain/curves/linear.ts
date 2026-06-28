/**
 * Linear curve: y = x.
 *
 * Progressão direta, sem aceleração. Útil quando o consumidor
 * (Animation Engine, Audio Engine) já aplica seu próprio easing.
 */

import type { CurveFn } from '../Curve';

export const linearCurve: CurveFn = (progress: number): number => {
  return progress;
};