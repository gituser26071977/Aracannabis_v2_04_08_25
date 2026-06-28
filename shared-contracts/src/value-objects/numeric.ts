/**
 * Numeric value objects — Duration, Timestamp, Percentage, Progress, indices.
 *
 * Each value object wraps a primitive with validation and semantic meaning.
 * All durations are stored in milliseconds (canonical unit).
 *
 * Conventions:
 *   - Duration:    milliseconds (integer), non-negative
 *   - Timestamp:   milliseconds since epoch (integer), non-negative
 *   - Percentage:  0..100 (number)
 *   - Progress:    0..1 (number)
 *   - CycleIndex:  non-negative integer
 *   - PhaseIndex:  non-negative integer
 */

import { AppError, isFiniteNumber, isInRange, isInteger, isNonEmptyString } from './validation';
import type { Brand } from './ids';

/** Maximum representable duration: 100 hours. */
export const MAX_DURATION_MS = 100 * 60 * 60 * 1000;
/** Maximum representable timestamp (year 9999). */
export const MAX_TIMESTAMP_MS = 253_402_300_799_000;

// =============================================================================
// Duration
// =============================================================================

export type Duration = Brand<number, 'Duration'>;

/**
 * Constructs a Duration in milliseconds. Throws if non-integer or out of range.
 */
export const Duration = (ms: number): Duration => {
  if (!isInteger(ms) || ms < 0 || ms > MAX_DURATION_MS) {
    throw new AppError(
      `Invalid Duration: must be integer in [0, ${MAX_DURATION_MS}]`,
      {
        code: 'invalid_duration',
        severity: 'warn',
        context: { ms },
      },
    );
  }
  return ms as Duration;
};

/**
 * Constructs a Duration from seconds.
 */
export const DurationFromSeconds = (seconds: number): Duration =>
  Duration(Math.round(seconds * 1000));

/**
 * Constructs a Duration from minutes.
 */
export const DurationFromMinutes = (minutes: number): Duration =>
  Duration(Math.round(minutes * 60_000));

export const DurationZero = (): Duration => 0 as Duration;

export const durationToSeconds = (d: Duration): number => d / 1000;
export const durationToMinutes = (d: Duration): number => d / 60_000;

// =============================================================================
// Timestamp
// =============================================================================

export type Timestamp = Brand<number, 'Timestamp'>;

/**
 * Constructs a Timestamp (milliseconds since epoch). Throws if invalid.
 */
export const Timestamp = (ms: number): Timestamp => {
  if (!isInteger(ms) || ms < 0 || ms > MAX_TIMESTAMP_MS) {
    throw new AppError(
      `Invalid Timestamp: must be integer in [0, ${MAX_TIMESTAMP_MS}]`,
      {
        code: 'invalid_timestamp',
        severity: 'warn',
        context: { ms },
      },
    );
  }
  return ms as Timestamp;
};

export const TimestampNow = (now: () => number = Date.now): Timestamp =>
  Timestamp(now());

export const timestampDifference = (later: Timestamp, earlier: Timestamp): Duration =>
  Duration(later - earlier);

// =============================================================================
// Percentage (0..100)
// =============================================================================

export type Percentage = Brand<number, 'Percentage'>;

export const Percentage = (value: number): Percentage => {
  if (!isFiniteNumber(value) || !isInRange(value, 0, 100)) {
    throw new AppError('Invalid Percentage: must be in [0, 100]', {
      code: 'invalid_percentage',
      severity: 'warn',
      context: { value },
    });
  }
  return value as Percentage;
};

// =============================================================================
// Progress (0..1)
// =============================================================================

export type Progress = Brand<number, 'Progress'>;

export const Progress = (value: number): Progress => {
  if (!isFiniteNumber(value) || !isInRange(value, 0, 1)) {
    throw new AppError('Invalid Progress: must be in [0, 1]', {
      code: 'invalid_progress',
      severity: 'warn',
      context: { value },
    });
  }
  return value as Progress;
};

export const ProgressFromPercentage = (p: Percentage): Progress =>
  Progress((p as number) / 100);

// =============================================================================
// CycleIndex
// =============================================================================

export type CycleIndex = Brand<number, 'CycleIndex'>;

export const CycleIndex = (value: number): CycleIndex => {
  if (!isInteger(value) || value < 0) {
    throw new AppError('Invalid CycleIndex: must be non-negative integer', {
      code: 'invalid_cycle_index',
      severity: 'warn',
      context: { value },
    });
  }
  return value as CycleIndex;
};

// =============================================================================
// PhaseIndex
// =============================================================================

export type PhaseIndex = Brand<number, 'PhaseIndex'>;

export const PhaseIndex = (value: number): PhaseIndex => {
  if (!isInteger(value) || value < 0) {
    throw new AppError('Invalid PhaseIndex: must be non-negative integer', {
      code: 'invalid_phase_index',
      severity: 'warn',
      context: { value },
    });
  }
  return value as PhaseIndex;
};

// =============================================================================
// Iso8601 (string timestamp in ISO 8601 format)
// =============================================================================

import { ISO8601_PATTERN } from './validation';

export type Iso8601 = Brand<string, 'Iso8601'>;

export const Iso8601 = (raw: string): Iso8601 => {
  if (!isNonEmptyString(raw) || !ISO8601_PATTERN.test(raw)) {
    throw new AppError('Invalid Iso8601: must be a valid ISO 8601 string', {
      code: 'invalid_iso8601',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as Iso8601;
};

export const Iso8601FromTimestamp = (ts: Timestamp): Iso8601 =>
  Iso8601(new Date(ts as number).toISOString());

export const Iso8601ToTimestamp = (iso: Iso8601): Timestamp =>
  Timestamp(Date.parse(iso as string));