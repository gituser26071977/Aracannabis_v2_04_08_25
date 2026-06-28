/**
 * BreathCycleConfig — configuração de uma sessão respiratória.
 *
 * Define durações em milissegundos para cada fase mecânica. Não carrega
 * nenhum significado clínico — protocolos como "4-7-8" ou "Box Breathing"
 * são expressos puramente como números aqui.
 *
 * Validações:
 *   - Todas as durações devem ser >= 0.
 *   - inhaleMs > 0 é obrigatório (uma sessão sem inalação não faz sentido).
 *   - exhaleMs > 0 é obrigatório (mesma razão).
 *   - cycles deve ser >= 1.
 *   - prepMs (opcional) deve ser >= 0; ausente = sem preparação.
 */

import { AppError } from '@shared/errors';

export interface BreathCycleConfig {
  readonly inhaleMs: number;
  readonly holdAfterInhaleMs: number;
  readonly exhaleMs: number;
  readonly holdAfterExhaleMs: number;
  readonly cycles: number;
  readonly prepMs?: number;
}

export const MIN_PHASE_MS = 0;
export const MIN_INHALE_MS = 1;
export const MIN_EXHALE_MS = 1;
export const MIN_CYCLES = 1;
export const MAX_CYCLES = 1_000;
export const MAX_PHASE_MS = 60 * 60 * 1000; // 1 hour

export const DEFAULT_BREATH_CYCLE_CONFIG: BreathCycleConfig = Object.freeze({
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 5,
  prepMs: 0,
});

export const isValidBreathCycleConfig = (config: BreathCycleConfig): boolean => {
  if (
    config.inhaleMs < MIN_INHALE_MS ||
    config.inhaleMs > MAX_PHASE_MS ||
    config.holdAfterInhaleMs < MIN_PHASE_MS ||
    config.holdAfterInhaleMs > MAX_PHASE_MS ||
    config.exhaleMs < MIN_EXHALE_MS ||
    config.exhaleMs > MAX_PHASE_MS ||
    config.holdAfterExhaleMs < MIN_PHASE_MS ||
    config.holdAfterExhaleMs > MAX_PHASE_MS
  ) {
    return false;
  }
  if (config.cycles < MIN_CYCLES || config.cycles > MAX_CYCLES) {
    return false;
  }
  if (config.prepMs !== undefined && (config.prepMs < MIN_PHASE_MS || config.prepMs > MAX_PHASE_MS)) {
    return false;
  }
  return true;
};

export const validateBreathCycleConfig = (config: BreathCycleConfig): void => {
  if (!isValidBreathCycleConfig(config)) {
    throw new AppError('Invalid BreathCycleConfig', {
      code: 'breath_invalid_config',
      severity: 'warn',
      context: { config },
    });
  }
};

/**
 * Returns the total duration of a single cycle in ms.
 */
export const computeCycleMs = (config: BreathCycleConfig): number => {
  return (
    config.inhaleMs + config.holdAfterInhaleMs + config.exhaleMs + config.holdAfterExhaleMs
  );
};

/**
 * Returns the total session duration (excluding prep) in ms.
 */
export const computeSessionMs = (config: BreathCycleConfig): number => {
  return computeCycleMs(config) * config.cycles;
};

/**
 * Returns the total session duration including prep in ms.
 */
export const computeTotalMs = (config: BreathCycleConfig): number => {
  return (config.prepMs ?? 0) + computeSessionMs(config);
};