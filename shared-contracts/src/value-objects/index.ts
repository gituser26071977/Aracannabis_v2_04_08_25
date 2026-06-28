/**
 * Value Objects — barrel.
 *
 * Branded primitives for unambiguous identity, time, and progress.
 *
 * Naming convention: each type has BOTH a type and a constructor with
 * the same name (TypeScript allows this via declaration merging). The
 * constructor validates input and throws on failure.
 */

export {
  AppError,
  ULID_PATTERN,
  ISO8601_PATTERN,
  SEMVER_PATTERN,
  UUID_V4_PATTERN,
  isNonEmptyString,
  isFiniteNumber,
  isInteger,
  isInRange,
  type AppErrorContext,
  type AppErrorOptions,
} from './validation';

export type { Brand } from './ids';
export {
  ProtocolId,
  SessionId,
  EngineId,
  TenantId,
  UserId,
  PatientId,
} from './ids';

export {
  Duration,
  DurationFromSeconds,
  DurationFromMinutes,
  DurationZero,
  durationToSeconds,
  durationToMinutes,
  MAX_DURATION_MS,
  Timestamp,
  TimestampNow,
  timestampDifference,
  MAX_TIMESTAMP_MS,
  Percentage,
  Progress,
  ProgressFromPercentage,
  CycleIndex,
  PhaseIndex,
  Iso8601,
  Iso8601FromTimestamp,
  Iso8601ToTimestamp,
} from './numeric';

export type {
  Duration,
  Timestamp,
  Percentage,
  Progress,
  CycleIndex,
  PhaseIndex,
  Iso8601,
} from './numeric';

export {
  SemanticVersion,
  parseSemanticVersion,
  compareSemanticVersions,
  isVersionCompatible,
} from './version';

export type { SemanticVersion as SemanticVersionType, ParsedVersion } from './version';