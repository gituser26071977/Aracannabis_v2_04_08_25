/**
 * AraFlow — Breath Engine (public API)
 *
 * Motor respiratório determinístico. Conhece APENAS mecânica
 * respiratória: phases, cycles, ratios, cadences, curves.
 *
 * Não conhece:
 *   - Box Breathing, Coherent Breathing, 4-7-8 (Protocol Engine).
 *   - Ansiedade, insônia (Protocol Engine).
 *   - UI, animação, áudio (Presentation Layer).
 *
 * Uso em produção:
 *   import { createBreathEngine } from '@core/breath-engine';
 *   const breath = createBreathEngine();
 *   breath.start();
 *   const off = breath.subscribe((e) => { ... });
 *
 * Dependência obrigatória: Timer Engine (única fonte oficial de tempo).
 *
 * Exports:
 *   - BreathEngine: classe principal
 *   - PhaseCalculator e DepthCalculator: funções puras reusáveis
 *   - Domain types: BreathPhase, BreathState, BreathCycleConfig, etc.
 *   - Curves: linear, easeIn, easeOut, easeInOut, sine, cosine, bezier
 */

export type {
  BreathPhase,
  BreathState,
  BreathCycleConfig,
  BreathRatio,
  BreathSnapshot,
  BreathEvent,
  BreathEventType,
  BreathListener,
  BreathUnsubscribe,
  CurveFn,
  CurveName,
} from './domain';

export {
  BREATH_PHASES,
  BREATH_PHASE_ORDER,
  nextPhase,
  BREATH_STATES,
  ACTIVE_BREATH_STATES,
  TERMINAL_BREATH_STATES,
  isActiveBreathState,
  isTerminalBreathState,
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
  computeBreathCadence,
  computeBreathRatio,
  formatBreathRatio,
  CURVE_NAMES,
  DEFAULT_CURVE_NAME,
  resolveCurve,
  EMPTY_BREATH_SNAPSHOT,
  BREATH_EVENT_TYPES,
  linearCurve,
  easeInCurve,
  easeOutCurve,
  easeInOutCurve,
  sineCurve,
  cosineCurve,
  bezierCurve,
} from './domain';

export {
  computePhaseInfo,
  type PhaseInfo,
  type SessionActivityState,
} from './application';

export { computeDepth } from './application';
export { BreathEngine, type BreathEngineDeps } from './application';

import type { BreathEngineDeps } from './application';
import { BreathEngine } from './application';

export const BREATH_ENGINE_VERSION = '1.0.0' as const;

/**
 * Factory para produção. Cria engine com deps validadas.
 * Caller é responsável por prover Timer Engine e MonotonicClock.
 */
export const createBreathEngine = (deps: BreathEngineDeps): BreathEngine => {
  return new BreathEngine(deps);
};