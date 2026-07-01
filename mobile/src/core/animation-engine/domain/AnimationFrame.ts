/**
 * AnimationFrame — immutable point-in-time projection of the
 * animation. The Animation Engine emits one AnimationFrame per
 * phase-change or per tick.
 *
 * All numeric fields are normalized to [0, 1] (except `timestamp`
 * and `remainingTime` which are milliseconds). This keeps the frame
 * shape simple and lets renderers (Sprint 9+) plug in any backend
 * (Skia, SVG, Lottie) without translation logic.
 *
 * Invariants:
 *   - radius ∈ [0, 1]
 *   - opacity ∈ [0, 1]
 *   - scale ∈ [0, 1]
 *   - normalizedProgress ∈ [0, 1] within the current phase
 *   - breathingDepth ∈ [0, 1] — current amplitude (peak = 1, trough = 0)
 *
 * Frames are deeply frozen on construction.
 */

import type { CurveName } from '@core/breath-engine';

import type { AnimationPhase } from './AnimationPhase';

export interface AnimationFrame {
  /** Capture time (monotonic ms). */
  readonly timestamp: number;
  /** Current animation phase. */
  readonly phase: AnimationPhase;
  /** Linear progress within the current phase, in [0, 1]. */
  readonly normalizedProgress: number;
  /** Visual radius of the breath circle, in [0, 1]. */
  readonly radius: number;
  /** Visual opacity, in [0, 1]. */
  readonly opacity: number;
  /** Visual scale (multiplier of base radius), in [0, 1]. */
  readonly scale: number;
  /** Easing curve applied to this frame. */
  readonly easingCurve: CurveName;
  /** Current breathing depth (0 = trough, 1 = peak). */
  readonly breathingDepth: number;
  /** Human-readable label. */
  readonly label: string;
  /** Remaining ms in current phase (or 0 for terminal). */
  readonly remainingTime: number;
}

/** Default labels per phase (re-exported for convenience). */
export const defaultLabelForPhase = (phase: AnimationPhase): string => {
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

/** Type guard (lightweight). */
export const isAnimationFrame = (v: unknown): v is AnimationFrame => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const f = v as Partial<AnimationFrame>;
  return (
    typeof f.timestamp === 'number' &&
    typeof f.phase === 'string' &&
    typeof f.normalizedProgress === 'number' &&
    typeof f.radius === 'number' &&
    typeof f.opacity === 'number' &&
    typeof f.scale === 'number' &&
    typeof f.easingCurve === 'string' &&
    typeof f.breathingDepth === 'number' &&
    typeof f.label === 'string' &&
    typeof f.remainingTime === 'number'
  );
};
