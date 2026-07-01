/**
 * @core/animation-engine — pure deterministic animation projection.
 *
 * Consumes Runtime / Breath / Timer / Session events and emits
 * immutable AnimationFrames. NO rendering, NO UI, NO React, NO
 * Skia/SVG/Lottie/Canvas.
 *
 * Sprint 8 deliverable. Sprint 9+ uses this engine to build the
 * visual experience.
 *
 * Version: 1.0.0
 */

// --- Domain ---
export {
  type AnimationPhase,
  ANIMATION_PHASES,
  ACTIVE_ANIMATION_PHASES,
  TERMINAL_ANIMATION_PHASES,
  isAnimationPhase,
  isActiveAnimationPhase,
  isTerminalAnimationPhase,
  labelForPhase,
} from './domain/AnimationPhase';
export {
  type AnimationFrame,
  defaultLabelForPhase,
  isAnimationFrame,
} from './domain/AnimationFrame';
export {
  type AnimationConfig,
  DEFAULT_ANIMATION_CONFIG,
  clamp,
  validateAnimationConfig,
} from './domain/AnimationConfig';
export {
  type AnimationEngineState,
  ANIMATION_ENGINE_STATES,
  TERMINAL_ANIMATION_ENGINE_STATES,
  isAnimationEngineState,
  isTerminalAnimationEngineState,
  legalAnimationEngineTransitions,
  canAnimationEngineTransition,
} from './domain/AnimationEngineState';
export {
  type AnimationEvent,
  type AnimationEventListener,
  type AnimationUnsubscribe,
  ANIMATION_EVENT_TYPES,
  isAnimationEvent,
} from './domain/AnimationEvent';
export { type AnimationMetrics, EMPTY_ANIMATION_METRICS } from './domain/AnimationMetrics';

// --- Application ---
import { AnimationEngine, ANIMATION_ENGINE_ID } from './application/AnimationEngine';
import type { AnimationEngineDeps } from './application/AnimationEngineDeps';
export { AnimationEngine, ANIMATION_ENGINE_ID };
export type { AnimationEngineDeps };
export {
  createAnimationEventStream,
  type AnimationEventStream,
} from './application/AnimationEventStream';

// --- Utilities ---
export {
  computeAnimationFrame,
  buildIdleFrame,
  type FrameComputationInput,
} from './util/frame-computation';
export {
  type HoldPosition,
  mapBreathPhase,
  mapSessionState,
  mapRuntimeState,
} from './util/phase-mapping';

// --- Version ---
export const ANIMATION_ENGINE_VERSION = '1.0.0' as const;

// --- Factory ---
export type CreateAnimationOptions = AnimationEngineDeps;

export const createAnimation = (deps: CreateAnimationOptions): AnimationEngine =>
  new AnimationEngine(deps);
