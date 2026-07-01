/**
 * phase-mapping — pure mappings between engine phases and animation
 * phases.
 *
 * The Animation Engine maps:
 *   - BreathEngine phases ('inhaling' | 'holdAfterInhale' | 'exhaling'
 *     | 'holdAfterExhale') → Animation phases
 *   - Session lifecycle states → Animation phases
 *   - Runtime states → Animation phases (defensive fallback)
 */

import type { BreathPhase } from '@core/breath-engine';

import type { AnimationPhase } from '../domain/AnimationPhase';

/** Whether the breath phase is at peak (held at the top of the cycle). */
export type HoldPosition = 'none' | 'peak' | 'trough';

/**
 * Map a BreathPhase to an AnimationPhase. The hold position is also
 * returned so callers can derive the breathing depth from the
 * intermediate amplitude.
 */
export const mapBreathPhase = (
  phase: BreathPhase,
): { readonly animation: 'inhale' | 'exhale' | 'hold'; readonly hold: HoldPosition } => {
  switch (phase) {
    case 'inhaling':
      return { animation: 'inhale', hold: 'none' };
    case 'holdAfterInhale':
      return { animation: 'hold', hold: 'peak' };
    case 'exhaling':
      return { animation: 'exhale', hold: 'none' };
    case 'holdAfterExhale':
      return { animation: 'hold', hold: 'trough' };
  }
};

/** Map a SessionState to an AnimationPhase (idle/preparing/running/completed). */
export const mapSessionState = (
  sessionState:
    | 'idle'
    | 'preparing'
    | 'running'
    | 'paused'
    | 'completed'
    | 'cancelled'
    | 'interrupted'
    | 'failed',
): AnimationPhase => {
  switch (sessionState) {
    case 'idle':
      return 'idle';
    case 'preparing':
      return 'preparing';
    case 'running':
    case 'paused':
    case 'interrupted':
      // Animation pauses with the session; runtime animation phase
      // is preserved by the engine via in-flight progress.
      return 'idle';
    case 'completed':
      return 'completed';
    case 'cancelled':
    case 'failed':
      return 'idle';
  }
};

/** Map a RuntimeState to an AnimationPhase (defensive fallback). */
export const mapRuntimeState = (
  runtimeState:
    | 'uninitialized'
    | 'loaded'
    | 'starting'
    | 'running'
    | 'paused'
    | 'stopping'
    | 'stopped'
    | 'completed'
    | 'errored'
    | 'disposed',
): AnimationPhase => {
  switch (runtimeState) {
    case 'uninitialized':
    case 'loaded':
    case 'stopped':
    case 'errored':
    case 'disposed':
      return 'idle';
    case 'starting':
      return 'preparing';
    case 'running':
    case 'paused':
    case 'stopping':
      return 'idle';
    case 'completed':
      return 'completed';
  }
};
