/**
 * Sine curve (ease-out sine): y = sin(x * π/2).
 *
 * Curva suave, derivada da metade de uma onda senoidal. Crescimento
 * rápido no início, desaceleração suave no fim.
 */

import type { CurveFn } from '../Curve';

export const sineCurve: CurveFn = (progress: number): number => {
  return Math.sin(progress * Math.PI * 0.5);
};