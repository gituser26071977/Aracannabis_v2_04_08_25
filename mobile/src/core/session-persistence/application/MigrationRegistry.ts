/**
 * MigrationRegistry — maps legacy schema versions to decoder-only
 * adapters that can emit the current shape.
 *
 * Used by PersistenceService on `load` when an adapter returns a
 * payload with `schemaVersion !== SERIALIZER_SCHEMA_VERSION`.
 *
 * Adding a migration:
 *   1. Bump SERIALIZER_SCHEMA_VERSION.
 *   2. Implement a `SessionDecoder` for the OLD version.
 *   3. Register it: registry.register(oldVersion, decoder).
 *
 * The registry is pure data — no I/O, no async.
 */

import type { SessionDecoder } from '../domain/SessionSerializer';

export interface MigrationRegistry {
  /** Register a decoder for a legacy version. */
  register(version: number, decoder: SessionDecoder): MigrationRegistry;

  /** Find a decoder for a given version. Returns undefined when missing. */
  find(version: number): SessionDecoder | undefined;

  /** List registered versions, sorted ascending. */
  versions(): readonly number[];
}

export const createMigrationRegistry = (
  initial: ReadonlyMap<number, SessionDecoder> = new Map(),
): MigrationRegistry => {
  const map = new Map<number, SessionDecoder>(initial);
  return {
    register(version, decoder) {
      map.set(version, decoder);
      return this;
    },
    find(version) {
      return map.get(version);
    },
    versions() {
      return Array.from(map.keys()).sort((a, b) => a - b);
    },
  };
};
