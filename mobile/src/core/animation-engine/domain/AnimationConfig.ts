/**
 * AnimationConfig — visual configuration knobs for the Animation
 * Engine. Each field is in [0, 1] (or a multiplier in [0, 2]).
 *
 * The default config matches a typical breath-circle: minimum radius
 * at idle, peak at full inhale, smooth opacity ramps.
 *
 * Sprint 9+ renderers may add their own presentation config — this
 * shape stays decoupled.
 */

import type { CurveName } from '@core/breath-engine';
import { DEFAULT_CURVE_NAME } from '@core/breath-engine';

export interface AnimationConfig {
  /** Easing curve applied to all frame interpolations. */
  readonly easingCurve: CurveName;
  /** Visual radius at idle (trough). Default 0.2. */
  readonly idleRadius: number;
  /** Visual radius at peak inhale. Default 1.0. */
  readonly peakRadius: number;
  /** Visual radius at trough exhale. Default 0.2. */
  readonly troughRadius: number;
  /** Opacity at idle. Default 0.4. */
  readonly idleOpacity: number;
  /** Opacity while in a breath phase. Default 1.0. */
  readonly activeOpacity: number;
  /** Opacity at completed state. Default 0.6. */
  readonly completedOpacity: number;
  /** Scale at idle (multiplier). Default 1.0. */
  readonly idleScale: number;
  /** Scale at peak inhale. Default 1.0. */
  readonly peakScale: number;
  /** Scale at trough exhale. Default 1.0. */
  readonly troughScale: number;
}

export const DEFAULT_ANIMATION_CONFIG: AnimationConfig = Object.freeze({
  easingCurve: DEFAULT_CURVE_NAME,
  idleRadius: 0.2,
  peakRadius: 1.0,
  troughRadius: 0.2,
  idleOpacity: 0.4,
  activeOpacity: 1.0,
  completedOpacity: 0.6,
  idleScale: 1.0,
  peakScale: 1.0,
  troughScale: 1.0,
});

/** Clamp a number to [min, max]. */
export const clamp = (n: number, min: number, max: number): number => {
  if (n < min) {
    return min;
  }
  if (n > max) {
    return max;
  }
  return n;
};

/** Validate an AnimationConfig. Throws on out-of-range values. */
export const validateAnimationConfig = (c: AnimationConfig): void => {
  const check = (name: string, n: number, min = 0, max = 1): void => {
    if (!Number.isFinite(n) || n < min || n > max) {
      throw new Error(
        `AnimationConfig.${name} must be in [${String(min)}, ${String(max)}], got ${String(n)}`,
      );
    }
  };
  check('idleRadius', c.idleRadius);
  check('peakRadius', c.peakRadius);
  check('troughRadius', c.troughRadius);
  check('idleOpacity', c.idleOpacity);
  check('activeOpacity', c.activeOpacity);
  check('completedOpacity', c.completedOpacity);
  check('idleScale', c.idleScale);
  check('peakScale', c.peakScale);
  check('troughScale', c.troughScale);
};
