/**
 * clock — minimal Clock implementation used by SimulationRuntime
 * and benchmarks.
 *
 * Wraps `Date.now()` for both monotonic and wall-now. Real monotonic
 * timing (used for drift measurement) is handled separately in the
 * benchmark module via `process.hrtime.bigint()`.
 */

import type { Clock } from '@araflow/shared-contracts';

export const createSystemClock = (): Clock => ({
  now: (): number => Date.now(),
  wallNow: (): number => Date.now(),
});

/**
 * Returns nanosecond-precision monotonic time. Used only by benchmarks.
 */
export const monotonicNowNs = (): bigint => process.hrtime.bigint();

/**
 * Returns current process memory usage in bytes. Used by benchmarks.
 */
export const memoryUsageBytes = (): number => process.memoryUsage().heapUsed;
