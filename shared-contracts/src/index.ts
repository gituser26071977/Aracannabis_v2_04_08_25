/**
 * AraFlow — Shared Contracts (Public API)
 *
 * Common language for all AraFlow engines and consumers. Every
 * engine must use these types as the canonical source for:
 *   - Identifier types (ProtocolId, SessionId, EngineId, etc.)
 *   - Time and progress value objects (Duration, Timestamp, etc.)
 *   - Canonical state and enum types (EngineState, BreathPhase, etc.)
 *   - Result/Option/Either patterns
 *   - Standard error hierarchy
 *   - Logger/Metrics/EventBus interfaces
 *   - Lifecycle interfaces (Engine, Disposable, Subscription)
 *
 * Rule: zero dependencies on framework (React, RN, Node, Browser).
 * Pure TypeScript only. 100% strict mode compatible.
 */

// Existing common types (preserved from Sprint 0)
export {
  PatientId as LegacyPatientId,
  SessionId as LegacySessionId,
  ProtocolId as LegacyProtocolId,
  ProtocolVersion,
  UserId as LegacyUserId,
  TenantId as LegacyTenantId,
  Iso8601 as LegacyIso8601,
  MonotonicMs,
  WallClockMs,
  Ok as LegacyOk,
  Err as LegacyErr,
  type Result as LegacyResult,
  type DiscriminatedUnion,
} from './common';

// Value Objects
export * from './value-objects';

// Enums
export * from './enums';

// Patterns
export * from './patterns';

// Utilities
export * from './utilities';

// Interfaces
export * from './interfaces';

// Events
export * from './events';

// Errors
export * from './errors';

// Existing protocol schemas (preserved for API DTOs)
export * from './protocol';
export * from './api';

/**
 * Version of the shared-contracts schema.
 */
export const SHARED_CONTRACTS_VERSION = '2.5.0' as const;