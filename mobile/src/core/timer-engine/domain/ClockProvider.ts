/**
 * ClockProvider — abstração sobre os mecanismos de scheduling do runtime.
 *
 * Por que abstrair?
 *   - Em produção: usa setTimeout/setInterval nativos.
 *   - Em testes: usa FakeClockProvider que permite controle determinístico.
 *   - Em wearables: pode usar APIs de menor precisão mas menor consumo.
 *
 * `setTimeout` agenda UM callback após `delayMs`.
 * `setInterval` agenda callbacks recorrentes a cada `periodMs`.
 *   - Implementações devem minimizar drift; se o runtime atrasar, o
 *     próximo callback deve ser agendado o mais cedo possível.
 */

import type { ClockHandle } from './ClockHandle';

export type ClockCallback = () => void;

export interface ClockProvider {
  /**
   * Schedules `callback` to fire after `delayMs` of clock time.
   * Returns a handle that can be used to cancel.
   */
  setTimeout(callback: ClockCallback, delayMs: number): ClockHandle;

  /**
   * Schedules `callback` to fire repeatedly, every `periodMs` of clock
   * time. Returns a handle that can be used to cancel.
   */
  setInterval(callback: ClockCallback, periodMs: number): ClockHandle;
}
