/**
 * Breath-related enums — canonical types for breath mechanics.
 *
 * IMPORTANT: The BreathPhase defined here is the CANONICAL type used
 * by all engines. The breath-engine has its own internal type which
 * happens to be structurally compatible; new engines (Protocol Engine,
 * Audio Engine, etc.) MUST use this enum.
 *
 * CurveType and InterpolationType describe how values progress over
 * time within a phase.
 */

import type { CurveFn } from './types';

// =============================================================================
// BreathPhase
// =============================================================================

export const BREATH_PHASES = [
  'inhaling',
  'holdAfterInhale',
  'exhaling',
  'holdAfterExhale',
] as const;

export type BreathPhase = (typeof BREATH_PHASES)[number];

export const isBreathPhase = (v: unknown): v is BreathPhase =>
  typeof v === 'string' && (BREATH_PHASES as readonly string[]).includes(v);

// =============================================================================
// CurveType
// =============================================================================

export const CURVE_TYPES = [
  'linear',
  'easeIn',
  'easeOut',
  'easeInOut',
  'sine',
  'cosine',
  'bezier',
] as const;

export type CurveType = (typeof CURVE_TYPES)[number];

export const isCurveType = (v: unknown): v is CurveType =>
  typeof v === 'string' && (CURVE_TYPES as readonly string[]).includes(v);

// =============================================================================
// InterpolationType
// =============================================================================

/**
 * How a value is interpolated between discrete points in time.
 * - 'discrete':   value changes instantly at each keypoint
 * - 'linear':     value changes linearly between keypoints
 * - 'curve':      value follows a curve (see CurveType) between keypoints
 */
export const INTERPOLATION_TYPES = ['discrete', 'linear', 'curve'] as const;

export type InterpolationType = (typeof INTERPOLATION_TYPES)[number];

export const isInterpolationType = (v: unknown): v is InterpolationType =>
  typeof v === 'string' && (INTERPOLATION_TYPES as readonly string[]).includes(v);

/**
 * Re-export of CurveFn type alias to avoid circular imports.
 */
export type { CurveFn } from './types';