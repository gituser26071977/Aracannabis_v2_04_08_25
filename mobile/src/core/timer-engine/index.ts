/**
 * AraFlow — Timer Engine (public API)
 *
 * Master clock da plataforma. Toda medição de tempo DEVE passar por
 * este engine. Nenhum outro módulo pode instanciar timers próprios.
 *
 * Exports:
 *   - TimerEngine: classe principal
 *   - Tipos públicos do domínio
 *   - Construtores de infraestrutura padrão
 *   - Construtores de fakes para testes (re-exportados de __tests__)
 *
 * Uso em produção:
 *   import { createTimerEngine } from '@core/timer-engine';
 *   const engine = createTimerEngine();
 *   engine.start();
 *   const off = engine.subscribe((e) => { ... });
 *
 * Uso em testes:
 *   import { createTestTimerEngine, FakeClockProvider } from '@core/timer-engine';
 */

export type {
  MonotonicClock,
  WallClock,
  ClockHandle,
  ClockProvider,
  ClockCallback,
  TimerMode,
  TimerState,
  DriftMeasurement,
  TimerEvent,
  TimerEventType,
  TimerListener,
  Unsubscribe,
} from './domain';

export {
  TIMER_MODE_TICK_INTERVAL_MS,
  DEFAULT_TIMER_MODE,
  TIMER_STATES,
  TIMER_EVENT_TYPES,
  MIN_TIME_SCALE,
  MAX_TIME_SCALE,
  DEFAULT_TIME_SCALE,
  isValidTimeScale,
} from './domain';

export { TimerEngine, type TimerEngineDeps, type TimerEngineSnapshot } from './application';
export { createEventDispatcher, type EventDispatcher } from './application';
export {
  createDriftCorrector,
  type DriftCorrectionStrategy,
  type ComputeNextDelayArgs,
  type RecordTickArgs,
} from './application';

export {
  createBrowserMonotonicClock,
  createBrowserWallClock,
  createDefaultClockProvider,
  type DefaultClockProviderOptions,
} from './infrastructure';

import { createBrowserMonotonicClock } from './infrastructure/BrowserMonotonicClock';
import { createBrowserWallClock } from './infrastructure/BrowserWallClock';
import { createDefaultClockProvider } from './infrastructure/DefaultClockProvider';
import { TimerEngine } from './application/TimerEngine';

/**
 * Factory para produção. Cria engine com adaptadores default
 * (performance.now, Date.now, setTimeout/setInterval).
 */
export const createTimerEngine = (): TimerEngine => {
  return new TimerEngine({
    monotonic: createBrowserMonotonicClock(),
    wall: createBrowserWallClock(),
    clockProvider: createDefaultClockProvider(),
  });
};

export const TIMER_ENGINE_VERSION = '1.0.0' as const;
