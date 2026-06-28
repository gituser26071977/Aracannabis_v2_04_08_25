/**
 * BreathRatio — razão entre fases dentro de um ciclo.
 *
 * Útil para descrição humana do ritmo (ex.: "1:1:1:1" para Box,
 * "4:7:8:0" para 4-7-8). Não tem significado clínico — é apenas
 * normalização.
 *
 * Importante: ratios são relativos dentro do ciclo, normalizados
 * para que inhale seja sempre 1.0. Isto facilita comparação entre
 * protocolos.
 */

import type { BreathCycleConfig } from './BreathCycleConfig';

export interface BreathRatio {
  readonly inhale: number;
  readonly holdAfterInhale: number;
  readonly exhale: number;
  readonly holdAfterExhale: number;
}

export const computeBreathRatio = (config: BreathCycleConfig): BreathRatio => {
  const { inhaleMs, holdAfterInhaleMs, exhaleMs, holdAfterExhaleMs } = config;
  if (inhaleMs <= 0) {
    return { inhale: 0, holdAfterInhale: 0, exhale: 0, holdAfterExhale: 0 };
  }
  return {
    inhale: 1,
    holdAfterInhale: holdAfterInhaleMs / inhaleMs,
    exhale: exhaleMs / inhaleMs,
    holdAfterExhale: holdAfterExhaleMs / inhaleMs,
  };
};

/**
 * Format ratio as a human-readable string. Examples:
 *   1:1:1:1   (Box)
 *   4:7:8:0   (4-7-8)
 *   1:0:1:0   (Coherent)
 */
export const formatBreathRatio = (ratio: BreathRatio): string => {
  const fmt = (n: number): string => {
    if (Number.isInteger(n)) {
      return n.toString();
    }
    return n.toFixed(2);
  };
  return `${fmt(ratio.inhale)}:${fmt(ratio.holdAfterInhale)}:${fmt(ratio.exhale)}:${fmt(ratio.holdAfterExhale)}`;
};