/**
 * BrowserMonotonicClock — implementação padrão de MonotonicClock
 * usando `performance.now()` quando disponível, com fallback
 * para `Date.now()` em ambientes sem performance API.
 *
 * Compatibilidade: React Native, Browsers modernos, Node 16+, Bun,
 * Deno, Web Workers, Service Workers. NÃO compatível com ambientes
 * síncronos sem event loop (ex.: scripts one-shot sem host).
 *
 * Nota sobre React Native: `performance.now()` é polyfilled e
 * disponível em todas as versões suportadas. Em caso de dúvida
 * em uma versão futura, o fallback cobre.
 */

import { AppError } from '@shared/errors';

import type { MonotonicClock } from '../domain';

interface PerformanceLike {
  now(): number;
}

const resolvePerformance = (): PerformanceLike | null => {
  if (typeof globalThis === 'undefined') {
    return null;
  }
  const perf = (globalThis as { performance?: PerformanceLike }).performance;
  if (perf !== undefined && typeof perf.now === 'function') {
    return perf;
  }
  return null;
};

export const createBrowserMonotonicClock = (): MonotonicClock => {
  const performanceApi = resolvePerformance();
  if (performanceApi === null) {
    throw new AppError('No monotonic clock available in this environment', {
      code: 'timer_no_monotonic_clock',
      severity: 'fatal',
    });
  }
  return {
    now: (): number => performanceApi.now(),
  };
};
