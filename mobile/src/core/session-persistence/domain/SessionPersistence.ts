/**
 * SessionPersistence — high-level seam between the Session Orchestrator
 * (or any caller) and the storage backend.
 *
 * Responsibilities:
 * - capture a Session into a snapshot
 * - serialize + persist + deserialize + reconstruct
 * - expose a list of recoverable sessions
 *
 * The Persistence implementation owns the serializer and adapter; the
 * interface hides both. Consumers (Orchestrator, future UI, future
 * sync layer) only depend on this interface.
 */

import type { SessionId } from '@araflow/shared-contracts';

import type { PersistedSessionSnapshot } from './SessionSnapshot';

export interface SaveInput {
  readonly sessionId: SessionId;
  readonly snapshot: PersistedSessionSnapshot;
  /** When true, save replaces any existing record for this session. */
  readonly overwrite?: boolean;
}

export type SaveResult =
  | { readonly ok: true; readonly sessionId: SessionId; readonly bytesWritten: number }
  | { readonly ok: false; readonly sessionId: SessionId; readonly reason: SaveFailureReason };

export type SaveFailureReason =
  | 'no-snapshot' // nothing to save
  | 'serialize-failed' // encoder rejected the input
  | 'storage-failed'; // adapter write failed

export type LoadResult =
  | {
      readonly ok: true;
      readonly sessionId: SessionId;
      readonly snapshot: PersistedSessionSnapshot;
      readonly bytesRead: number;
    }
  | { readonly ok: false; readonly sessionId: SessionId; readonly reason: LoadFailureReason };

export type LoadFailureReason =
  | 'not-found' // no record for this session
  | 'corrupted' // payload present but invalid
  | 'incompatible' // schema version not supported
  | 'storage-failed'; // adapter read failed

export interface SessionPersistence {
  readonly persistenceId: string;

  /** Persist a snapshot for a session. Async. */
  save(input: SaveInput): Promise<SaveResult>;

  /** Load a snapshot for a session. Returns not-found when missing. */
  load(sessionId: SessionId): Promise<LoadResult>;

  /** Delete the persisted snapshot. No-op when missing. */
  delete(sessionId: SessionId): Promise<void>;

  /** Probe whether a snapshot exists. */
  exists(sessionId: SessionId): Promise<boolean>;

  /** List all session ids currently stored. */
  list(): Promise<readonly SessionId[]>;

  /** Clear every persisted snapshot. Destructive. */
  clear(): Promise<void>;
}
