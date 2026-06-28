/**
 * Domain — barrel.
 *
 * Pure types and interfaces. Zero runtime side effects, zero
 * dependencies on platform, framework, or I/O.
 */

export type { MonotonicClock } from './MonotonicClock';
export type { WallClock } from './WallClock';
export type { ClockHandle } from './ClockHandle';
export type { ClockProvider, ClockCallback } from './ClockProvider';
export type { TimerMode } from './TimerMode';
export { TIMER_MODE_TICK_INTERVAL_MS, DEFAULT_TIMER_MODE } from './TimerMode';
export type { TimerState } from './TimerState';
export { TIMER_STATES } from './TimerState';
export type { DriftMeasurement } from './DriftMeasurement';
export type { TimerEvent, TimerEventType } from './TimerEvent';
export { TIMER_EVENT_TYPES } from './TimerEvent';
export {
  MIN_TIME_SCALE,
  MAX_TIME_SCALE,
  DEFAULT_TIME_SCALE,
  isValidTimeScale,
} from './TimeScale';
export type { TimerListener, Unsubscribe } from './Listener';
