/**
 * SessionSerializer — converts a snapshot to/from a transport-safe
 * string. The serializer is the only place that knows the wire format.
 *
 * Requirements (per Sprint 7 brief):
 * - deterministic (same input → same bytes)
 * - no precision loss (no JSON.stringify truncation)
 * - version field at top level (migrations live elsewhere)
 * - cross-version compatible via `MigrationRegistry`
 *
 * The default `JsonSerializer` produces a deterministic UTF-8 string
 * with sorted keys. No BigInt, no Date (timestamps are passed as
 * numbers; branded strings are passed as strings).
 */

import type { PersistedSessionSnapshot } from './SessionSnapshot';

/** Current serializer schema. Bump on breaking payload changes. */
export const SERIALIZER_SCHEMA_VERSION = 1 as const;

/** Top-level wrapper persisted by the default JSON serializer. */
export interface SerializedSnapshot {
  readonly schemaVersion: typeof SERIALIZER_SCHEMA_VERSION;
  readonly snapshot: PersistedSessionSnapshot;
}

export interface SessionSerializer {
  /** Stable identifier of this serializer (e.g. 'json-v1'). */
  readonly serializerId: string;

  /** Schema version this serializer emits. */
  readonly schemaVersion: number;

  /** Encode a snapshot into an opaque string. */
  encode(snapshot: PersistedSessionSnapshot): string;

  /** Decode an opaque string into a snapshot. Throws on corruption. */
  decode(encoded: string): PersistedSessionSnapshot;
}

/**
 * Decoder-only interface used by migration pathways. Decoders
 * validate the schema version and throw on mismatch unless the
 * migration is handled upstream.
 */
export interface SessionDecoder {
  readonly schemaVersion: number;
  decode(encoded: string): PersistedSessionSnapshot;
}
