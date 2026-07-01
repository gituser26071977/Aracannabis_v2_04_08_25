/**
 * PersistenceService — default implementation of SessionPersistence.
 *
 * Owns a SessionSerializer + a StorageAdapter + a MigrationRegistry.
 * Wire flow on save:
 *
 *   snapshot → serialize (with schema version envelope)
 *           → adapter.write(sessionId, payload)
 *
 * Wire flow on load:
 *
 *   adapter.read(sessionId) → payload
 *     → parse envelope (rejects on bad JSON or missing schemaVersion)
 *     → if schemaVersion matches current, decode via serializer
 *     → else look up decoder in MigrationRegistry; if found, decode
 *     → else return incompatible
 */

import type { SessionId } from '@araflow/shared-contracts';

import type { MigrationRegistry } from './MigrationRegistry';
import type {
  SessionPersistence,
  SaveInput,
  SaveResult,
  LoadResult,
} from '../domain/SessionPersistence';
import { SERIALIZER_SCHEMA_VERSION } from '../domain/SessionSerializer';
import type { SessionSerializer } from '../domain/SessionSerializer';
import type { PersistedSessionSnapshot } from '../domain/SessionSnapshot';
import type { StorageAdapter } from '../domain/StorageAdapter';

export const PERSISTENCE_SERVICE_ID = 'persistence-service-v1' as const;

export interface PersistenceServiceDeps {
  readonly serializer: SessionSerializer;
  readonly storage: StorageAdapter;
  readonly migrations?: MigrationRegistry;
}

interface Envelope {
  readonly schemaVersion: number;
  readonly snapshot?: unknown;
}

const isEnvelope = (v: unknown): v is Envelope => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  return typeof (v as { schemaVersion?: unknown }).schemaVersion === 'number';
};

export const createPersistenceService = (deps: PersistenceServiceDeps): SessionPersistence => {
  const migrations = deps.migrations;

  const encode = (snapshot: PersistedSessionSnapshot): string => {
    return deps.serializer.encode(snapshot);
  };

  const decodeEnvelope = (encoded: string): PersistedSessionSnapshot => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(encoded);
    } catch (err) {
      throw new Error(`PersistenceService: invalid JSON (${(err as Error).message})`);
    }
    if (!isEnvelope(parsed)) {
      throw new Error('PersistenceService: payload is missing schemaVersion envelope');
    }
    if (parsed.schemaVersion === deps.serializer.schemaVersion) {
      return deps.serializer.decode(encoded);
    }
    const migrationDecoder = migrations?.find(parsed.schemaVersion);
    if (migrationDecoder !== undefined) {
      return migrationDecoder.decode(encoded);
    }
    throw new Error(
      `PersistenceService: schemaVersion ${String(parsed.schemaVersion)} is not supported by current serializer (${String(deps.serializer.schemaVersion)}) and no migration is registered`,
    );
  };

  return {
    persistenceId: PERSISTENCE_SERVICE_ID,

    async save(input: SaveInput): Promise<SaveResult> {
      try {
        const payload = encode(input.snapshot);
        await deps.storage.write(input.sessionId, payload, {
          ...(input.overwrite === undefined ? {} : { overwrite: input.overwrite }),
        });
        return {
          ok: true,
          sessionId: input.sessionId,
          bytesWritten: payload.length,
        };
      } catch (err) {
        const message = (err as Error).message ?? '';
        const reason = message.includes('JsonSerializer')
          ? 'serialize-failed'
          : message.includes('already exists')
            ? 'serialize-failed'
            : 'storage-failed';
        return { ok: false, sessionId: input.sessionId, reason };
      }
    },

    async load(sessionId: SessionId): Promise<LoadResult> {
      try {
        const result = await deps.storage.read(sessionId);
        if (result.payload === null) {
          return { ok: false, sessionId, reason: 'not-found' };
        }
        let snapshot: PersistedSessionSnapshot;
        try {
          snapshot = decodeEnvelope(result.payload);
        } catch (err) {
          const message = (err as Error).message ?? '';
          if (message.includes('not supported') || message.includes('incompatible')) {
            return { ok: false, sessionId, reason: 'incompatible' };
          }
          return { ok: false, sessionId, reason: 'corrupted' };
        }
        return {
          ok: true,
          sessionId,
          snapshot,
          bytesRead: result.payload.length,
        };
      } catch {
        return { ok: false, sessionId, reason: 'storage-failed' };
      }
    },

    async delete(sessionId: SessionId): Promise<void> {
      await deps.storage.delete(sessionId);
    },

    async exists(sessionId: SessionId): Promise<boolean> {
      return deps.storage.exists(sessionId);
    },

    async list(): Promise<readonly SessionId[]> {
      const keys = await deps.storage.list();
      return keys as readonly SessionId[];
    },

    async clear(): Promise<void> {
      await deps.storage.clear();
    },
  };
};

export const CURRENT_SCHEMA_VERSION = SERIALIZER_SCHEMA_VERSION;
