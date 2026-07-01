/**
 * volume-math — pure helpers for volume calculation.
 *
 * No side effects. No timers. No I/O. Used by both the Engine
 * (effective-volume calculation when forwarding to the adapter) and
 * tests (volume invariants).
 */

/** Clamp a value into [0, 1]. NaN propagates (returns NaN). */
export const clamp01 = (v: number): number => Math.max(0, Math.min(1, v));

/**
 * Effective linear volume for a layer.
 *
 *   effective = muted ? 0 : clamp01(master) * clamp01(layer)
 *
 * Guarantees: result ∈ [0, 1] when `master` and `layer` are finite.
 * NaN inputs propagate (caller's responsibility).
 */
export const effectiveVolume = (master: number, layer: number, muted: boolean): number => {
  if (muted) {
    return 0;
  }
  return clamp01(master) * clamp01(layer);
};

/**
 * Convert a linear amplitude in [0, 1] to decibels. Returns `-Infinity`
 * for 0 (full silence). Useful for adapters that need dB FS.
 */
export const linearToDecibels = (linear: number): number => {
  if (linear <= 0) {
    return Number.NEGATIVE_INFINITY;
  }
  return 20 * Math.log10(clamp01(linear));
};

/**
 * Convert decibels to linear amplitude in [0, 1]. `-Infinity` maps to 0.
 */
export const decibelsToLinear = (db: number): number => {
  if (!Number.isFinite(db)) {
    return 0;
  }
  return clamp01(Math.pow(10, db / 20));
};