/**
 * DriftMeasurement — registro de uma medição de drift.
 *
 * O Timer Engine mede drift comparando tempo monotônico decorrido
 * com o número de ticks que deveriam ter ocorrido.
 *
 *   drift = actualElapsed - expectedElapsed
 *
 * Drift positivo = ticks atrasados (runtime sobrecarregado).
 * Drift negativo = ticks adiantados (raro em prática).
 *
 * Acumulado (cumulativeDrift) é a soma de todos os drifts
 * normalizada por tick. Drift acumulado deve tender a zero.
 */

export interface DriftMeasurement {
  readonly tickIndex: number;
  readonly actualElapsedMs: number;
  readonly expectedElapsedMs: number;
  readonly driftMs: number;
  readonly cumulativeDriftMs: number;
}
