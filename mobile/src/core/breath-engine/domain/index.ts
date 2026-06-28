/**
 * Domain — barrel.
 *
 * Pure types and interfaces. Zero runtime side effects, zero
 * dependencies on platform, framework, or I/O. Only depends on
 * @shared/errors for validation throws.
 */

export type { BreathPhase } from './BreathPhase';
export { BREATH_PHASES, BREATH_PHASE_ORDER, nextPhase } from './BreathPhase';

export type { BreathState } from './BreathState';
export {
  BREATH_STATES,
  ACTIVE_BREATH_STATES,
  TERMINAL_BREATH_STATES,
  isActiveBreathState,
  isTerminalBreathState,
} from './BreathState';

export type { BreathCycleConfig } from './BreathCycleConfig';
export {
  MIN_PHASE_MS,
  MIN_INHALE_MS,
  MIN_EXHALE_MS,
  MIN_CYCLES,
  MAX_CYCLES,
  MAX_PHASE_MS,
  DEFAULT_BREATH_CYCLE_CONFIG,
  isValidBreathCycleConfig,
  validateBreathCycleConfig,
  computeCycleMs,
  computeSessionMs,
  computeTotalMs,
} from './BreathCycleConfig';

export { computeBreathCadence } from './BreathCadence';

export type { BreathRatio } from './BreathRatio';
export { computeBreathRatio, formatBreathRatio } from './BreathRatio';

export type { CurveFn, CurveName } from './Curve';
export { CURVE_NAMES, DEFAULT_CURVE_NAME, resolveCurve } from './Curve';

export {
  linearCurve,
  easeInCurve,
  easeOutCurve,
  easeInOutCurve,
  sineCurve,
  cosineCurve,
  bezierCurve,
} from './curves';

export type { BreathSnapshot } from './BreathSnapshot';
export { EMPTY_BREATH_SNAPSHOT } from './BreathSnapshot';

export type { BreathEvent, BreathEventType } from './BreathEvent';
export { BREATH_EVENT_TYPES } from './BreathEvent';

export type { BreathListener, BreathUnsubscribe } from './Listener';