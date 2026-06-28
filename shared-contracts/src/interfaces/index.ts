/**
 * Interfaces — barrel.
 */

export type {
  Disposable,
  Subscription,
  Engine,
  LifecycleController,
} from './lifecycle';

export type {
  Clock,
  Scheduler,
  ScheduledTask,
  TaskCallback,
  MonotonicMs,
  WallClockMs,
} from './infrastructure';

export type {
  Logger,
  LogContext,
  LogEntry,
  MetricsCollector,
  Counter,
  Gauge,
  Histogram,
  MetricValue,
  MetricLabels,
  Event,
  EventListener,
  EventBus,
} from './observability';

export type {
  ProtocolSource,
  ProtocolSourceFormat,
  ProtocolSourceLoader,
  ExecutionPlan,
  PhaseStep,
  CompilerResult,
  ValidationResult,
  Compiler,
} from './protocol';