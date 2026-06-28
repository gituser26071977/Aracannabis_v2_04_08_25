/**
 * BreathCadence — métrica derivada do BreathCycleConfig.
 *
 * Cadence é o número de ciclos completos por minuto. É puramente
 * informativo — o engine opera em milissegundos; cadence é uma forma
 * human-friendly de expressar ritmo.
 *
 * Fórmula: 60_000ms / cycleMs
 *
 * Para Box Breathing (4-4-4-4 = 16000ms): cadence = 60000/16000 = 3.75 BPM.
 * Para Coherent (5-0-5-0 = 10000ms): cadence = 60000/10000 = 6 BPM.
 * Para 4-7-8 (4-7-8-0 = 19000ms): cadence ≈ 3.16 BPM.
 */

import type { BreathCycleConfig } from './BreathCycleConfig';
import { computeCycleMs } from './BreathCycleConfig';

export const computeBreathCadence = (config: BreathCycleConfig): number => {
  const cycleMs = computeCycleMs(config);
  if (cycleMs <= 0) {
    return 0;
  }
  return 60_000 / cycleMs;
};