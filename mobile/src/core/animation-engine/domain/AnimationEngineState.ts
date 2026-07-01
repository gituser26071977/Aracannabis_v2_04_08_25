/**
 * AnimationEngineState — internal FSM of the Animation Engine.
 *
 * Distinct from RuntimeState (10 states) and SessionState (8 states).
 * The Animation Engine has its own minimal FSM because its
 * responsibilities are narrower (idle / preparing / running / paused
 * / disposed).
 *
 *   idle      — created, no session attached
 *   running   — session attached, frames emitting on events
 *   paused    — session paused, frames frozen at last value
 *   disposed  — terminal, no further emissions
 */

export type AnimationEngineState = 'idle' | 'running' | 'paused' | 'disposed';

export const ANIMATION_ENGINE_STATES: readonly AnimationEngineState[] = [
  'idle',
  'running',
  'paused',
  'disposed',
] as const;

export const TERMINAL_ANIMATION_ENGINE_STATES: readonly AnimationEngineState[] = [
  'disposed',
] as const;

export const isAnimationEngineState = (v: unknown): v is AnimationEngineState =>
  typeof v === 'string' && (ANIMATION_ENGINE_STATES as readonly string[]).includes(v);

export const isTerminalAnimationEngineState = (s: AnimationEngineState): boolean =>
  (TERMINAL_ANIMATION_ENGINE_STATES as readonly AnimationEngineState[]).includes(s);

/** Legal transitions. */
export const legalAnimationEngineTransitions = (
  from: AnimationEngineState,
): readonly AnimationEngineState[] => {
  switch (from) {
    case 'idle':
      return ['running', 'disposed'];
    case 'running':
      return ['paused', 'idle', 'disposed'];
    case 'paused':
      return ['running', 'idle', 'disposed'];
    case 'disposed':
      return [];
  }
};

export const canAnimationEngineTransition = (
  from: AnimationEngineState,
  to: AnimationEngineState,
): boolean =>
  (legalAnimationEngineTransitions(from) as readonly AnimationEngineState[]).includes(to);
