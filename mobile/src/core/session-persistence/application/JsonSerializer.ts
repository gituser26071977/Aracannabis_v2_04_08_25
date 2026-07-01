/**
 * JsonSerializer — default SessionSerializer implementation.
 *
 * Uses `deterministic-json` to produce byte-stable output with sorted
 * keys. The encoded string is wrapped in a top-level envelope
 * carrying the schema version; migrations live in
 * `MigrationRegistry`.
 *
 * Wire format (version 1):
 *
 *   {
 *     "schemaVersion": 1,
 *     "snapshot": { ... PersistedSessionSnapshot ... }
 *   }
 *
 * Round-trip is lossless for any JSON-safe value. Branded strings
 * (SessionId, ProtocolId, ExecutionPlanId) are passed through as
 * plain strings — they're already strings at runtime.
 */

import {
  SERIALIZER_SCHEMA_VERSION,
  type SerializedSnapshot,
  type SessionSerializer,
} from '../domain/SessionSerializer';
import type { PersistedSessionSnapshot } from '../domain/SessionSnapshot';
import { parseDeterministic, stringifyDeterministic } from '../util/deterministic-json';

export const JSON_SERIALIZER_ID = 'json-v1' as const;

export const createJsonSerializer = (): SessionSerializer => ({
  serializerId: JSON_SERIALIZER_ID,
  schemaVersion: SERIALIZER_SCHEMA_VERSION,

  encode(snapshot: PersistedSessionSnapshot): string {
    const envelope: SerializedSnapshot = {
      schemaVersion: SERIALIZER_SCHEMA_VERSION,
      snapshot,
    };
    return stringifyDeterministic(envelope);
  },

  decode(encoded: string): PersistedSessionSnapshot {
    const parsed = parseDeterministic<unknown>(encoded);
    if (typeof parsed !== 'object' || parsed === null) {
      throw new Error('JsonSerializer.decode: payload is not an object');
    }
    const obj = parsed as Partial<SerializedSnapshot>;
    if (typeof obj.schemaVersion !== 'number') {
      throw new Error('JsonSerializer.decode: missing schemaVersion');
    }
    if (obj.schemaVersion !== SERIALIZER_SCHEMA_VERSION) {
      throw new Error(
        `JsonSerializer.decode: schemaVersion ${String(obj.schemaVersion)} not supported (expected ${String(SERIALIZER_SCHEMA_VERSION)})`,
      );
    }
    if (typeof obj.snapshot !== 'object' || obj.snapshot === null) {
      throw new Error('JsonSerializer.decode: missing snapshot');
    }
    return obj.snapshot as PersistedSessionSnapshot;
  },
});
