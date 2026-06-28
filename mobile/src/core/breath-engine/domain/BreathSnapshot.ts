/**
 * BreathSnapshot — visão read-only do estado do Breath Engine.
 *
 * Consumidores (Animation Engine, UI layer) lêem este snapshot para
 * renderizar frames. O snapshot é uma fotografia completa do estado
 * em um instante.
 *
 * Invariantes:
 *   - phaseProgress ∈ [0, 1]
 *   - cycleProgress ∈ [0, 1]
 *   - depth ∈ [0, 1]
 *   - phaseRemainingMs ≥ 0
 *   - totalRemainingMs ≥ 0
 */

import type { BreathPhase } from './BreathPhase';
import type { BreathState } from './BreathState';

export interface BreathSnapshot {
  readonly state: BreathState;
  readonly phase: BreathPhase | null;
  readonly cycleIndex: number;
  readonly totalCycles: number;
  readonly cycleProgress: number;
  readonly phaseProgress: number;
  readonly phaseElapsedMs: number;
  readonly phaseRemainingMs: number;
  readonly totalElapsedMs: number;
  readonly totalRemainingMs: number;
  readonly depth: number;
  readonly curveName: string;
}

export const EMPTY_BREATH_SNAPSHOT: BreathSnapshot = Object.freeze({
  state: 'idle',
  phase: null,
  cycleIndex: 0,
  totalCycles: 0,
  cycleProgress: 0,
  phaseProgress: 0,
  phaseElapsedMs: 0,
  phaseRemainingMs: 0,
  totalElapsedMs: 0,
  totalRemainingMs: 0,
  depth: 0,
  curveName: 'easeInOut',
});