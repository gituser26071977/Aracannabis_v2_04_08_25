/**
 * DepthCalculator — função pura que computa a "profundidade"
 * respiratória atual (0..1) dados a fase, progresso na fase,
 * e curva.
 *
 * Modelo:
 *   - Inalação: profundidade sobe de 0 a 1 seguindo a curva.
 *   - HoldAfterInhale: profundidade = 1 (constante).
 *   - Exalação: profundidade desce de 1 a 0 seguindo 1 - curva.
 *   - HoldAfterExhale: profundidade = 0 (constante).
 *   - Null (prep ou completed): profundidade = 0.
 *
 * A curva é aplicada à fase ativa. Para a exalação, a curva é
 * invertida (1 - curva) — isso mantém a sensação de "subir suave"
 * durante a inalação e "descer suave" durante a exalação quando
 * se usa easeInOut como curva default.
 *
 * IMPORTANTE: progress é clampado a [0, 1] para tolerar imprecisões
 * de ponto flutuante fora do range.
 */

import type { BreathPhase, CurveFn } from '../domain';

const clamp01 = (n: number): number => {
  if (n < 0) return 0;
  if (n > 1) return 1;
  return n;
};

export const computeDepth = (
  phase: BreathPhase | null,
  phaseProgress: number,
  curve: CurveFn,
): number => {
  if (phase === null) {
    return 0;
  }
  const p = clamp01(phaseProgress);
  switch (phase) {
    case 'inhaling':
      return curve(p);
    case 'holdAfterInhale':
      return 1;
    case 'exhaling':
      return 1 - curve(p);
    case 'holdAfterExhale':
      return 0;
  }
};