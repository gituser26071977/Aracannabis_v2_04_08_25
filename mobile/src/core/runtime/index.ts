/**
 * @core/runtime — AraFlow Runtime Facade.
 *
 * Single public API for the AraFlow Core. Composes TimerEngine,
 * BreathEngine, and ProtocolRuntime behind a 12-method API.
 *
 * Version: 1.0.0 — frozen upon completion of Sprint 4.
 * Consumers must NOT import any engine directly. Always go through Runtime.
 */

export { RuntimeEngine } from './application/RuntimeEngine';
export type { RuntimeEngineDeps } from './application/RuntimeEngineDeps';
export {
  createRuntimeEventStream,
  type RuntimeEventStream,
} from './application/RuntimeEventStream';

// --- Domain types ---
export {
  type RuntimeState,
  RUNTIME_STATES,
  TERMINAL_RUNTIME_STATES,
  isRuntimeState,
  isTerminalRuntimeState,
} from './domain/RuntimeState';
export {
  type RuntimeEvent,
  type RuntimeEventListener,
  type RuntimeUnsubscribe,
  type RuntimeEventSource,
  RUNTIME_EVENT_SOURCES,
  isRuntimeEventSource,
} from './domain/RuntimeEvent';
export {
  type RuntimeLifecycleEvent,
  type RuntimeLifecycleEventType,
  RUNTIME_LIFECYCLE_EVENT_TYPES,
  isRuntimeLifecycleEventType,
} from './domain/RuntimeLifecycleEvent';
export type { RuntimeSnapshot } from './domain/RuntimeSnapshot';
export type { RuntimeMetrics, EventCounters } from './domain/RuntimeMetrics';

// --- Utilities (re-exported from util/) ---
export { createTimerLikeAdapter } from './util/timer-like-adapter';
export { planToBreathConfig } from './util/plan-to-breath-config';
export {
  aggregateMetrics,
  EMPTY_EVENT_COUNTERS,
  type AggregateMetricsInput,
} from './util/aggregate-metrics';

// --- Factory + version ---
export const RUNTIME_ENGINE_VERSION = '1.0.0' as const;
