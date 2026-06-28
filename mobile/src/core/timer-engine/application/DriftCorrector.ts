/**
 * DriftCorrector — calcula o ajuste necessário ao próximo tick para
 * compensar drift acumulado.
 *
 * Modelo:
 *   - Engine emite tick events em intervalos regulares `intervalMs`.
 *   - Runtime atrasa callbacks por alguma quantidade `deltaMs`.
 *   - Após cada tick:
 *       actualElapsed   = monotonicNow() - sessionStartedAt
 *       expectedElapsed = (tickIndex + 1) * intervalMs
 *       drift           = actualElapsed - expectedElapsed
 *   - Para compensar, o próximo tick é agendado com:
 *       nextDelay = max(1, intervalMs - drift)
 *
 * Isso significa: se o runtime atrasou 5ms no tick N, o tick N+1 é
 * agendado 5ms mais cedo, eventualmente compensando.
 *
 * Drift cumulativo é exposto via `cumulativeDriftMs` no evento `drift`
 * emitido a cada medição significativa (>= 1ms).
 *
 * Limitação conhecida: drift só pode ser compensado para FRENTE
 * (i.e., catching up). Se o runtime atrasar tanto que a sessão
 * ultrapasse `expectedElapsed + intervalMs`, o engine emite
 * catch-up via `foregrounded` event mas o drift local deste tick
 * permanece registrado.
 */

import type { DriftMeasurement, MonotonicClock } from '../domain';

export interface DriftCorrectionStrategy {
  /**
   * Given the parameters, returns the delay to use for the next tick.
   * Always returns a positive integer (>= 1ms).
   */
  computeNextDelayMs(args: ComputeNextDelayArgs): number;

  /**
   * Records a tick measurement and returns the drift observation
   * (or null if the measurement is not significant enough to report).
   */
  recordTick(args: RecordTickArgs): DriftMeasurement | null;
}

export interface ComputeNextDelayArgs {
  readonly intervalMs: number;
  readonly previousDriftMs: number;
  readonly previousNextDelayMs: number;
  readonly actualElapsedMs: number;
}

export interface RecordTickArgs {
  readonly tickIndex: number;
  readonly intervalMs: number;
  readonly actualElapsedMs: number;
}

const SIGNIFICANT_DRIFT_MS = 1; // Only emit drift event if drift >= 1ms

const createDefaultStrategy = (clock: MonotonicClock): DriftCorrectionStrategy => {
  void clock; // Reserved for future use (e.g., time-based smoothing).

  let cumulativeDriftMs = 0;

  const recordTick = (args: RecordTickArgs): DriftMeasurement | null => {
    const expectedElapsedMs = (args.tickIndex + 1) * args.intervalMs;
    const driftMs = args.actualElapsedMs - expectedElapsedMs;
    cumulativeDriftMs += driftMs;

    if (Math.abs(driftMs) < SIGNIFICANT_DRIFT_MS) {
      return null;
    }

    return {
      tickIndex: args.tickIndex,
      actualElapsedMs: args.actualElapsedMs,
      expectedElapsedMs,
      driftMs,
      cumulativeDriftMs,
    };
  };

  const computeNextDelayMs = (args: ComputeNextDelayArgs): number => {
    // Compensate previous drift; clamp to [1, intervalMs * 2] to avoid
    // degenerate negative delays (when runtime is far behind) and
    // degenerate long delays (when runtime is far ahead).
    const proposed = args.intervalMs - args.previousDriftMs;
    return Math.max(1, Math.min(args.intervalMs * 2, Math.round(proposed)));
  };

  return { computeNextDelayMs, recordTick };
};

export const createDriftCorrector = (clock: MonotonicClock): DriftCorrectionStrategy => {
  return createDefaultStrategy(clock);
};
