/**
 * Shared branded types — re-exports from contracts.
 *
 * Mantemos uma cópia em shared/ para evitar acoplamento direto com
 * shared-contracts em UI/presentation. Engenheiros podem usar qualquer
 * um; o compilador trata como idêntico por structural typing.
 */

export type {
  PatientId,
  SessionId,
  ProtocolId,
  ProtocolVersion,
  UserId,
  TenantId,
  Iso8601,
  MonotonicMs,
  WallClockMs,
  Result,
} from '@contracts/common';
