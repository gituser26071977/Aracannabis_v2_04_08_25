/**
 * Common types and branded primitives.
 *
 * Branded types (TYPESTRs) impedem mixing acidental de tipos semanticamente
 * diferentes que partilham o mesmo tipo primitivo TS. Ex.: um `PatientId` e
 * um `SessionId` são ambos `string` em runtime, mas são tipos distintos
 * em tempo de compilação.
 */

declare const brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [brand]: B };

export type PatientId = Brand<string, 'PatientId'>;
export type SessionId = Brand<string, 'SessionId'>;
export type ProtocolId = Brand<string, 'ProtocolId'>;
export type ProtocolVersion = Brand<string, 'ProtocolVersion'>;
export type UserId = Brand<string, 'UserId'>;
export type TenantId = Brand<string, 'TenantId'>;

export type Iso8601 = Brand<string, 'Iso8601'>;
export type MonotonicMs = Brand<number, 'MonotonicMs'>;
export type WallClockMs = Brand<number, 'WallClockMs'>;

/**
 * Construtores seguros para branded types.
 * Usar sempre que precisar converter uma primitiva em tipo nominal.
 */
export const PatientId = (raw: string): PatientId => raw as PatientId;
export const SessionId = (raw: string): SessionId => raw as SessionId;
export const ProtocolId = (raw: string): ProtocolId => raw as ProtocolId;
export const ProtocolVersion = (raw: string): ProtocolVersion => raw as ProtocolVersion;
export const UserId = (raw: string): UserId => raw as UserId;
export const TenantId = (raw: string): TenantId => raw as TenantId;
export const Iso8601 = (raw: string): Iso8601 => raw as Iso8601;
export const MonotonicMs = (raw: number): MonotonicMs => raw as MonotonicMs;
export const WallClockMs = (raw: number): WallClockMs => raw as WallClockMs;

/**
 * Result type — para casos onde queremos evitar throw.
 * Inspirado em Rust's Result<T, E>.
 */
export type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const Ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
export const Err = <E>(error: E): Result<never, E> => ({ ok: false, error });

/**
 * Discriminated union helper.
 */
export type DiscriminatedUnion<T, K extends keyof T> = T extends Record<K, infer V> ? T : never;
