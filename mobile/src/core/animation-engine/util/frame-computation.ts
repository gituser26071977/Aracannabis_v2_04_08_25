/**
 * frame-computation — pure projection from engine inputs to an
 * AnimationFrame.
 *
 * Inputs:
 *   - AnimationPhase
 *   - normalized progress (0..1) within the phase
 *   - Hold position (only relevant when phase = 'hold')
 *   - AnimationConfig (visual knobs)
 *   - Easing curve
 *   - timestamp
 *   - remainingTime
 *
 * Output: a deeply-frozen AnimationFrame.
 *
 * The projection is pure: same inputs → same output. No I/O, no
 * subscriptions, no engine state.
 */

import { resolveCurve } from '@core/breath-engine';

import type { HoldPosition } from './phase-mapping';
import type { AnimationConfig } from '../domain/AnimationConfig';
import { clamp } from '../domain/AnimationConfig';
import type { AnimationFrame } from '../domain/AnimationFrame';
import { defaultLabelForPhase } from '../domain/AnimationFrame';
import type { AnimationPhase } from '../domain/AnimationPhase';

export interface FrameComputationInput {
  readonly phase: AnimationPhase;
  /** Linear progress within the phase, clamped to [0, 1]. */
  readonly normalizedProgress: number;
  /** Hold position (only used when phase = 'hold'). */
  readonly hold: HoldPosition;
  readonly config: AnimationConfig;
  readonly timestamp: number;
  readonly remainingTime: number;
}

const safeCurve = (name: AnimationConfig['easingCurve']) => {
  try {
    return resolveCurve(name);
  } catch {
    return (p: number): number => p;
  }
};

/** Compute the breathing depth (0 = trough, 1 = peak) for the frame. */
const computeBreathingDepth = (
  phase: AnimationPhase,
  progress: number,
  hold: HoldPosition,
): number => {
  const eased = clamp(progress, 0, 1);
  switch (phase) {
    case 'inhale':
      return eased;
    case 'exhale':
      return 1 - eased;
    case 'hold':
      return hold === 'trough' ? 0 : 1;
    case 'idle':
    case 'preparing':
      return 0;
    case 'completed':
      return 0;
  }
};

/** Compute visual radius from breathing depth + config. */
const computeRadius = (phase: AnimationPhase, depth: number, config: AnimationConfig): number => {
  switch (phase) {
    case 'idle':
    case 'preparing':
      return clamp(config.idleRadius, 0, 1);
    case 'inhale': {
      const t = clamp(depth, 0, 1);
      return clamp(config.troughRadius + (config.peakRadius - config.troughRadius) * t, 0, 1);
    }
    case 'hold':
      return clamp(depth === 0 ? config.troughRadius : config.peakRadius, 0, 1);
    case 'exhale': {
      const t = clamp(depth, 0, 1);
      // `depth` for exhale decreases from 1 → 0 as the lung empties;
      // we still want higher depth → larger radius (depth semantics
      // are "how full the lung is", shared with inhale).
      return clamp(config.troughRadius + (config.peakRadius - config.troughRadius) * t, 0, 1);
    }
    case 'completed':
      return clamp(config.idleRadius, 0, 1);
  }
};

/** Compute visual opacity. */
const computeOpacity = (
  phase: AnimationPhase,
  progress: number,
  config: AnimationConfig,
): number => {
  switch (phase) {
    case 'idle':
      return clamp(config.idleOpacity, 0, 1);
    case 'preparing': {
      const t = clamp(progress, 0, 1);
      return clamp(config.idleOpacity + (config.activeOpacity - config.idleOpacity) * t, 0, 1);
    }
    case 'inhale':
    case 'hold':
    case 'exhale':
      return clamp(config.activeOpacity, 0, 1);
    case 'completed':
      return clamp(config.completedOpacity, 0, 1);
  }
};

/** Compute visual scale. */
const computeScale = (phase: AnimationPhase, depth: number, config: AnimationConfig): number => {
  switch (phase) {
    case 'idle':
    case 'preparing':
    case 'completed':
      return clamp(config.idleScale, 0, 1);
    case 'inhale': {
      const t = clamp(depth, 0, 1);
      return clamp(config.troughScale + (config.peakScale - config.troughScale) * t, 0, 1);
    }
    case 'hold':
      return clamp(depth === 0 ? config.troughScale : config.peakScale, 0, 1);
    case 'exhale': {
      const t = clamp(depth, 0, 1);
      return clamp(config.troughScale + (config.peakScale - config.troughScale) * t, 0, 1);
    }
  }
};

/**
 * Compute an AnimationFrame from inputs. Pure function.
 */
export const computeAnimationFrame = (input: FrameComputationInput): AnimationFrame => {
  const curve = safeCurve(input.config.easingCurve);
  const easedProgress = clamp(curve(clamp(input.normalizedProgress, 0, 1)), 0, 1);
  const depth = computeBreathingDepth(input.phase, easedProgress, input.hold);
  const radius = computeRadius(input.phase, depth, input.config);
  const opacity = computeOpacity(input.phase, easedProgress, input.config);
  const scale = computeScale(input.phase, depth, input.config);
  const label = defaultLabelForPhase(input.phase);

  return Object.freeze({
    timestamp: input.timestamp,
    phase: input.phase,
    normalizedProgress: clamp(input.normalizedProgress, 0, 1),
    radius: clamp(radius, 0, 1),
    opacity: clamp(opacity, 0, 1),
    scale: clamp(scale, 0, 1),
    easingCurve: input.config.easingCurve,
    breathingDepth: clamp(depth, 0, 1),
    label,
    remainingTime: Math.max(0, input.remainingTime),
  });
};

/**
 * Build an idle frame at construction time.
 */
export const buildIdleFrame = (config: AnimationConfig, timestamp: number): AnimationFrame =>
  computeAnimationFrame({
    phase: 'idle',
    normalizedProgress: 0,
    hold: 'none',
    config,
    timestamp,
    remainingTime: 0,
  });
