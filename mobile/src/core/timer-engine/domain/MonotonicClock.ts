/**
 * AraFlow — Timer Engine (Domain)
 *
 * MonotonicClock — interface para um relógio cuja progressão é
 * estritamente não-decrescente. Imune a mudanças de wall clock
 * (manuais, NTP sync, daylight saving, etc.).
 *
 * Princípios:
 *   - `now() >= now() - ε` para qualquer chamada subsequente.
 *   - Não correlacionado com tempo civil.
 *   - Sub-millisecond precision é desejável mas não obrigatória.
 *
 * Implementações:
 *   - BrowserMonotonicClock (usa performance.now)
 *   - NodeMonotonicClock (usa performance.now ou process.hrtime)
 *   - FakeMonotonicClock (para testes, controlado pelo test runner)
 */

export interface MonotonicClock {
  /**
   * Returns elapsed milliseconds since the clock's reference point.
   * Reference point is implementation-defined (page load, process start,
   * worker init, etc.) — call sites must treat the value as opaque.
   */
  now(): number;
}
