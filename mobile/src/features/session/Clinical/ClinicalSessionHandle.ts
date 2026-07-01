/**
 * ClinicalSessionHandle — the public seam for the ClinicalSession.
 *
 * The handle owns the runtime/animation/audio/session/orchestrator
 * lifecycle, exposes pure read accessors (status, frame, remaining
 * time, protocol metadata), and routes control calls to the
 * appropriate Core engine.
 *
 * No React, no RN, no AsyncStorage here — the handle is a pure
 * TypeScript orchestrator surface. The screen drives it via
 * `requestAnimationFrame` for visual updates.
 */

import type { AnimationFrame } from '@core/animation-engine';

export type ClinicalSessionStatus =
  | 'idle'
  | 'starting'
  | 'running'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'errored'
  | 'disposed';

export interface ClinicalSessionHandle {
  readonly status: () => ClinicalSessionStatus;
  readonly currentFrame: () => AnimationFrame | null;
  /**
   * Refresh the underlying animation frame from the current clock.
   * The screen calls this from its rAF tick. Safe to call at any
   * cadence. Returns the refreshed frame, or `null` if the
   * session is disposed.
   */
  readonly update: () => AnimationFrame | null;
  readonly remainingMs: () => number;
  readonly totalDurationMs: () => number;
  readonly protocolTitle: () => string;
  readonly protocolId: () => string;
  readonly startedAtIso: () => string | null;
  readonly completedNaturally: () => boolean;
  readonly start: () => void;
  readonly pause: () => void;
  readonly resume: () => void;
  readonly stop: () => Promise<void>;
  readonly dispose: () => Promise<void>;
}
