/**
 * AnimationMetrics — derived read model of the Animation Engine.
 *
 * Counters and timestamps. Useful for benchmarking, drift detection,
 * and observability in Sprint 9+.
 */

export interface AnimationMetrics {
  readonly framesEmitted: number;
  readonly updates: number;
  readonly phaseChanges: number;
  readonly lastFrameTimestamp: number | null;
  readonly attachedSince: number | null;
}

export const EMPTY_ANIMATION_METRICS: AnimationMetrics = Object.freeze({
  framesEmitted: 0,
  updates: 0,
  phaseChanges: 0,
  lastFrameTimestamp: null,
  attachedSince: null,
});
