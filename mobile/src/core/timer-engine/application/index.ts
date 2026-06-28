/**
 * Application — barrel.
 *
 * Pure orchestration: state machine, event dispatch, drift correction.
 * No platform-specific code; only consumes domain interfaces.
 */

export { createEventDispatcher, type EventDispatcher } from './EventEmitter';
export {
  createDriftCorrector,
  type DriftCorrectionStrategy,
  type ComputeNextDelayArgs,
  type RecordTickArgs,
} from './DriftCorrector';
export { TimerEngine, type TimerEngineDeps, type TimerEngineSnapshot } from './TimerEngine';
