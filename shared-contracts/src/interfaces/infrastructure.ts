/**
 * Infrastructure interfaces — Clock, Scheduler.
 *
 * These describe the time-related infrastructure that all engines
 * depend on. Implementations live in @core/timer-engine.
 */

import type { Brand } from '../value-objects/ids';

/**
 * Clock — source of monotonic time. Returns milliseconds since an
 * arbitrary epoch (typically process start).
 */
export interface Clock {
  /**
   * Returns the current monotonic time in milliseconds.
   */
  now(): number;

  /**
   * Returns the current wall-clock time in milliseconds since Unix epoch.
   */
  wallNow(): number;
}

export type MonotonicMs = Brand<number, 'MonotonicMs'>;
export type WallClockMs = Brand<number, 'WallClockMs'>;

/**
 * ScheduledTask — opaque handle returned by Scheduler.
 */
export interface ScheduledTask {
  /**
   * Cancels the scheduled task. Idempotent.
   */
  cancel(): void;

  /**
   * Returns true if the task is still scheduled (not yet fired or cancelled).
   */
  readonly active: boolean;
}

export type TaskCallback = () => void;

/**
 * Scheduler — abstraction over setTimeout/setInterval.
 */
export interface Scheduler {
  /**
   * Schedules a callback to fire once after `delayMs`.
   * Returns a handle that can be used to cancel.
   */
  setTimeout(callback: TaskCallback, delayMs: number): ScheduledTask;

  /**
   * Schedules a callback to fire every `periodMs`.
   * Returns a handle that can be used to cancel.
   */
  setInterval(callback: TaskCallback, periodMs: number): ScheduledTask;
}