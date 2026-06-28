/**
 * PhaseCalculator — função pura que determina a fase respiratória
 * atual dado o config e o tempo decorrido.
 *
 * Esta função NÃO toca em estado, NÃO emite eventos, NÃO tem
 * side effects. É uma representação matemática do ciclo respiratório
 * e pode ser usada em qualquer lugar (testes, UI, Protocol Engine).
 *
 * Modelo do ciclo:
 *
 *   [prepMs opcional] [inhale] [holdAfterInhale] [exhale] [holdAfterExhale] × cycles
 *
 * PhaseInfo.activity:
 *   - 'preparing' : dentro de prepMs (phase = null)
 *   - 'active'    : dentro de uma das 4 fases mecânicas
 *   - 'completed' : sessionElapsedMs >= sessionDurationMs (phase = null)
 *
 * Quando activity === 'completed', cycleIndex === config.cycles
 * (um a mais que o último índice válido 0..cycles-1).
 */

import type { BreathCycleConfig, BreathPhase } from '../domain';
import { computeCycleMs, computeSessionMs } from '../domain';

export type SessionActivityState = 'preparing' | 'active' | 'completed';

export interface PhaseInfo {
  readonly activity: SessionActivityState;
  readonly phase: BreathPhase | null;
  readonly cycleIndex: number;
  readonly phaseElapsedMs: number;
  readonly phaseDurationMs: number;
  readonly phaseProgress: number;
  readonly phaseRemainingMs: number;
  readonly cycleElapsedMs: number;
  readonly cycleDurationMs: number;
  readonly cycleProgress: number;
  readonly sessionElapsedMs: number;
  readonly sessionDurationMs: number;
  readonly sessionRemainingMs: number;
  readonly totalElapsedMs: number;
  readonly totalDurationMs: number;
  readonly totalRemainingMs: number;
}

const clampNonNegative = (n: number): number => (n < 0 ? 0 : n);

export const computePhaseInfo = (
  config: BreathCycleConfig,
  totalElapsedMs: number,
): PhaseInfo => {
  const prepMs = config.prepMs ?? 0;
  const cycleDurationMs = computeCycleMs(config);
  const sessionDurationMs = computeSessionMs(config);
  const totalDurationMs = prepMs + sessionDurationMs;
  const safeElapsed = clampNonNegative(totalElapsedMs);

  // 1) Preparing phase.
  if (safeElapsed < prepMs) {
    return {
      activity: 'preparing',
      phase: null,
      cycleIndex: 0,
      phaseElapsedMs: safeElapsed,
      phaseDurationMs: prepMs,
      phaseProgress: prepMs > 0 ? safeElapsed / prepMs : 1,
      phaseRemainingMs: prepMs - safeElapsed,
      cycleElapsedMs: 0,
      cycleDurationMs,
      cycleProgress: 0,
      sessionElapsedMs: 0,
      sessionDurationMs,
      sessionRemainingMs: sessionDurationMs,
      totalElapsedMs: safeElapsed,
      totalDurationMs,
      totalRemainingMs: totalDurationMs - safeElapsed,
    };
  }

  const sessionElapsedMs = safeElapsed - prepMs;

  // 2) Completed session.
  if (sessionElapsedMs >= sessionDurationMs) {
    return {
      activity: 'completed',
      phase: null,
      cycleIndex: config.cycles,
      phaseElapsedMs: 0,
      phaseDurationMs: 0,
      phaseProgress: 1,
      phaseRemainingMs: 0,
      cycleElapsedMs: cycleDurationMs,
      cycleDurationMs,
      cycleProgress: 1,
      sessionElapsedMs: sessionDurationMs,
      sessionDurationMs,
      sessionRemainingMs: 0,
      totalElapsedMs: totalDurationMs,
      totalDurationMs,
      totalRemainingMs: 0,
    };
  }

  // 3) Active phase within a cycle.
  const cycleIndex = Math.floor(sessionElapsedMs / cycleDurationMs);
  const cycleElapsedMs = sessionElapsedMs - cycleIndex * cycleDurationMs;

  let phase: BreathPhase;
  let phaseElapsedMs: number;
  let phaseDurationMs: number;

  if (cycleElapsedMs < config.inhaleMs) {
    phase = 'inhaling';
    phaseElapsedMs = cycleElapsedMs;
    phaseDurationMs = config.inhaleMs;
  } else if (cycleElapsedMs < config.inhaleMs + config.holdAfterInhaleMs) {
    phase = 'holdAfterInhale';
    phaseElapsedMs = cycleElapsedMs - config.inhaleMs;
    phaseDurationMs = config.holdAfterInhaleMs;
  } else if (
    cycleElapsedMs <
    config.inhaleMs + config.holdAfterInhaleMs + config.exhaleMs
  ) {
    phase = 'exhaling';
    phaseElapsedMs = cycleElapsedMs - config.inhaleMs - config.holdAfterInhaleMs;
    phaseDurationMs = config.exhaleMs;
  } else {
    phase = 'holdAfterExhale';
    phaseElapsedMs =
      cycleElapsedMs - config.inhaleMs - config.holdAfterInhaleMs - config.exhaleMs;
    phaseDurationMs = config.holdAfterExhaleMs;
  }

  const phaseProgress = phaseDurationMs > 0 ? phaseElapsedMs / phaseDurationMs : 1;
  const phaseRemainingMs = Math.max(0, phaseDurationMs - phaseElapsedMs);
  const cycleProgress = cycleElapsedMs / cycleDurationMs;

  return {
    activity: 'active',
    phase,
    cycleIndex,
    phaseElapsedMs,
    phaseDurationMs,
    phaseProgress,
    phaseRemainingMs,
    cycleElapsedMs,
    cycleDurationMs,
    cycleProgress,
    sessionElapsedMs,
    sessionDurationMs,
    sessionRemainingMs: sessionDurationMs - sessionElapsedMs,
    totalElapsedMs: safeElapsed,
    totalDurationMs,
    totalRemainingMs: totalDurationMs - safeElapsed,
  };
};