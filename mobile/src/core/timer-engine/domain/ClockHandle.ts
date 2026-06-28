/**
 * ClockHandle — token retornado por setTimeout/setInterval.
 *
 * Permite cancelar um agendamento. Cancelamento é idempotente.
 */

export interface ClockHandle {
  /**
   * Cancels the scheduled callback. Idempotent — calling more than
   * once is a no-op.
   */
  cancel(): void;

  /**
   * Returns true if the callback has not yet fired and has not been
   * cancelled. False after firing or cancellation.
   */
  isActive(): boolean;
}
