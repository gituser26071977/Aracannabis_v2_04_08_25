/**
 * AnimationPhase — the visible phase of the animation.
 *
 * Distinct from `BreathPhase` (engine-level mechanical phases). The
 * Animation Engine maps Breath phases to a coarser, presentation-level
 * taxonomy:
 *
 *   Breath 'inhaling'        → Animation 'inhale'
 *   Breath 'holdAfterInhale' → Animation 'hold'   (held at peak)
 *   Breath 'exhaling'        → Animation 'exhale'
 *   Breath 'holdAfterExhale' → Animation 'hold'   (held at trough)
 *
 * Plus session lifecycle phases:
 *
 *   'idle'       — pre-session
 *   'preparing'  — session started but not yet in first cycle
 *   'completed'  — session reached its natural end
 *
 * The `hold` state carries the peak/trough distinction via
 * `breathingDepth` (0..1) so renderers don't need to track it.
 */

export type AnimationPhase = 'idle' | 'preparing' | 'inhale' | 'hold' | 'exhale' | 'completed';

export const ANIMATION_PHASES: readonly AnimationPhase[] = [
  'idle',
  'preparing',
  'inhale',
  'hold',
  'exhale',
  'completed',
] as const;

export const ACTIVE_ANIMATION_PHASES: readonly AnimationPhase[] = [
  'idle',
  'preparing',
  'inhale',
  'hold',
  'exhale',
] as const;

export const TERMINAL_ANIMATION_PHASES: readonly AnimationPhase[] = ['completed'] as const;

export const isAnimationPhase = (v: unknown): v is AnimationPhase =>
  typeof v === 'string' && (ANIMATION_PHASES as readonly string[]).includes(v);

export const isActiveAnimationPhase = (phase: AnimationPhase): boolean =>
  (ACTIVE_ANIMATION_PHASES as readonly AnimationPhase[]).includes(phase);

export const isTerminalAnimationPhase = (phase: AnimationPhase): boolean =>
  (TERMINAL_ANIMATION_PHASES as readonly AnimationPhase[]).includes(phase);

/** Human-readable label for the phase. */
export const labelForPhase = (phase: AnimationPhase): string => {
  switch (phase) {
    case 'idle':
      return 'Ready';
    case 'preparing':
      return 'Get ready';
    case 'inhale':
      return 'Breathe in';
    case 'hold':
      return 'Hold';
    case 'exhale':
      return 'Breathe out';
    case 'completed':
      return 'Complete';
  }
};
