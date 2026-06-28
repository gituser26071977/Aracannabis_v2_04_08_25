/**
 * Cosine curve (ease-in-out): y = (1 - cos(x * π)) / 2.
 *
 * Simétrico em torno de x = 0.5. Curva S clássica de meio ciclo senoidal.
 * Suave em ambos os extremos.
 */

import type { CurveFn } from '../Curve';

export const cosineCurve: CurveFn = (progress: number): number => {
  return (1 - Math.cos(progress * Math.PI)) / 2;
};