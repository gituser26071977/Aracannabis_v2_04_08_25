/**
 * EaseInOut curve: combines easeIn for first half, easeOut for second half.
 *
 *   - For 0 ≤ x ≤ 0.5: y = 2 * x^2
 *   - For 0.5 < x ≤ 1: y = 1 - 2 * (1 - x)^2
 *
 * Smooth start, smooth end. Modelo clássico para respiração — entrada
 * gradual, plateau, saída gradual. Curva default do Breath Engine.
 */

import type { CurveFn } from '../Curve';

export const easeInOutCurve: CurveFn = (progress: number): number => {
  if (progress < 0.5) {
    return 2 * progress * progress;
  }
  const inv = 1 - progress;
  return 1 - 2 * inv * inv;
};