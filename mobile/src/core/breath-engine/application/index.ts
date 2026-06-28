/**
 * Application — barrel.
 *
 * Pure orchestration: state machine, event dispatch, phase/depth
 * computation. No platform-specific code; only consumes domain types
 * and depends on Timer Engine (via injection).
 */

export {
  createBreathEventDispatcher,
  type BreathEventDispatcher,
} from './EventDispatcher';

export {
  computePhaseInfo,
  type PhaseInfo,
  type SessionActivityState,
} from './PhaseCalculator';

export { computeDepth } from './DepthCalculator';

export { BreathEngine, type BreathEngineDeps } from './BreathEngine';