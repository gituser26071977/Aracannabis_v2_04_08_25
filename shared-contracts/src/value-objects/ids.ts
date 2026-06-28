/**
 * Core identifiers — branded types for unambiguous identity.
 *
 * Each ID is a `string` at runtime but a distinct type at compile time.
 * Constructors validate format and throw on invalid input.
 *
 * Format conventions:
 *   - ProtocolId:  ULID (lexicographically sortable, 26 chars)
 *   - SessionId:   ULID
 *   - EngineId:    kebab-case string, e.g., "timer-engine", "breath-engine"
 *   - TenantId:    ULID
 *   - UserId:      ULID
 */

import { AppError, ULID_PATTERN, isNonEmptyString } from './validation';

/**
 * Branded identifier type.
 */
export type Brand<T, B extends string> = T & { readonly __brand: B };

export type ProtocolId = Brand<string, 'ProtocolId'>;
export type SessionId = Brand<string, 'SessionId'>;
export type EngineId = Brand<string, 'EngineId'>;
export type TenantId = Brand<string, 'TenantId'>;
export type UserId = Brand<string, 'UserId'>;
export type PatientId = Brand<string, 'PatientId'>;

/**
 * Constructs a ProtocolId from a string. Throws on invalid ULID.
 */
export const ProtocolId = (raw: string): ProtocolId => {
  if (!isNonEmptyString(raw) || !ULID_PATTERN.test(raw)) {
    throw new AppError('Invalid ProtocolId: must be a non-empty ULID', {
      code: 'invalid_protocol_id',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as ProtocolId;
};

/**
 * Constructs a SessionId from a string. Throws on invalid ULID.
 */
export const SessionId = (raw: string): SessionId => {
  if (!isNonEmptyString(raw) || !ULID_PATTERN.test(raw)) {
    throw new AppError('Invalid SessionId: must be a non-empty ULID', {
      code: 'invalid_session_id',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as SessionId;
};

/**
 * Constructs an EngineId from a string. Throws on invalid kebab-case format.
 */
export const EngineId = (raw: string): EngineId => {
  if (!isNonEmptyString(raw) || !/^[a-z][a-z0-9-]*[a-z0-9]$/.test(raw)) {
    throw new AppError(
      'Invalid EngineId: must be kebab-case starting with letter',
      {
        code: 'invalid_engine_id',
        severity: 'warn',
        context: { raw },
      },
    );
  }
  return raw as EngineId;
};

export const TenantId = (raw: string): TenantId => {
  if (!isNonEmptyString(raw) || !ULID_PATTERN.test(raw)) {
    throw new AppError('Invalid TenantId: must be a non-empty ULID', {
      code: 'invalid_tenant_id',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as TenantId;
};

export const UserId = (raw: string): UserId => {
  if (!isNonEmptyString(raw) || !ULID_PATTERN.test(raw)) {
    throw new AppError('Invalid UserId: must be a non-empty ULID', {
      code: 'invalid_user_id',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as UserId;
};

export const PatientId = (raw: string): PatientId => {
  if (!isNonEmptyString(raw) || !ULID_PATTERN.test(raw)) {
    throw new AppError('Invalid PatientId: must be a non-empty ULID', {
      code: 'invalid_patient_id',
      severity: 'warn',
      context: { raw },
    });
  }
  return raw as PatientId;
};