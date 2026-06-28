/**
 * Observability interfaces — Logger, MetricsCollector, Event, EventBus.
 *
 * Logger: structured logging.
 * MetricsCollector: counters, gauges, histograms.
 * Event: base type for all events flowing through EventBus.
 * EventBus: type-safe pub/sub.
 */

import type { Subscription } from './lifecycle';
import type { Severity } from '../enums/priority';
import type { Priority } from '../enums/priority';
import type { EngineId } from '../value-objects/ids';

// =============================================================================
// Logger
// =============================================================================

export interface LogContext {
  readonly [key: string]: unknown;
}

export interface LogEntry {
  readonly timestamp: number;
  readonly severity: Severity;
  readonly message: string;
  readonly engineId?: EngineId;
  readonly context: LogContext;
}

/**
 * Logger — structured logging interface.
 *
 * Implementations: ConsoleLogger (mobile/web), RingBufferLogger (in-memory
 * for testing), RemoteLogger (AraOS backend).
 */
export interface Logger {
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
  fatal(message: string, context?: LogContext): void;
  log(entry: LogEntry): void;
}

// =============================================================================
// MetricsCollector
// =============================================================================

export type MetricValue = number;
export type MetricLabels = Readonly<Record<string, string>>;

export interface Counter {
  readonly name: string;
  readonly value: number;
  readonly labels: MetricLabels;
}

export interface Gauge {
  readonly name: string;
  readonly value: number;
  readonly labels: MetricLabels;
}

export interface Histogram {
  readonly name: string;
  readonly count: number;
  readonly sum: number;
  readonly min: number;
  readonly max: number;
  readonly mean: number;
  readonly labels: MetricLabels;
}

/**
 * MetricsCollector — counters, gauges, histograms.
 *
 * Implementations are platform-specific (e.g., StatsD, Prometheus).
 */
export interface MetricsCollector {
  incrementCounter(name: string, value?: number, labels?: MetricLabels): void;
  setGauge(name: string, value: number, labels?: MetricLabels): void;
  recordHistogram(name: string, value: number, labels?: MetricLabels): void;
  getCounter(name: string, labels?: MetricLabels): Counter | null;
  getGauge(name: string, labels?: MetricLabels): Gauge | null;
  getHistogram(name: string, labels?: MetricLabels): Histogram | null;
  reset(): void;
}

// =============================================================================
// Event
// =============================================================================

/**
 * Event — base shape of all events flowing through EventBus.
 */
export interface Event {
  readonly type: string;
  readonly monotonicMs: number;
  readonly priority?: Priority;
  readonly engineId?: EngineId;
  readonly payload?: Readonly<Record<string, unknown>>;
}

export type EventListener<T extends Event = Event> = (event: T) => void;

// =============================================================================
// EventBus
// =============================================================================

/**
 * EventBus — type-safe pub/sub with priority support.
 */
export interface EventBus<T extends Event = Event> {
  publish(event: T): void;
  subscribe(type: string, listener: EventListener<T>): Subscription;
  subscribeAll(listener: EventListener<T>): Subscription;
  listenerCount(type?: string): number;
  clear(): void;
}