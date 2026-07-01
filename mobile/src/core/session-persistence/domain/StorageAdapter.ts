/**
 * StorageAdapter — abstract storage seam.
 *
 * Adapters are responsible for storing opaque strings keyed by
 * sessionId. They do not interpret the payload. This keeps adapters
 * trivial to implement (in-memory, AsyncStorage, SQLite, IndexedDB,
 * filesystem) and lets the PersistenceService own serialization.
 *
 * All methods are async to keep a single async contract across
 * adapters — in-memory adapters return resolved promises immediately.
 *
 * The adapter does not validate `payload`. Callers must serialize
 * before calling `write`, and must validate after `read`.
 */

export interface StorageWriteOptions {
  /** When true, the write replaces any existing record. */
  readonly overwrite?: boolean;
}

export interface StorageReadResult {
  /** The stored payload, or null if no record exists. */
  readonly payload: string | null;
  /** Monotonic timestamp at which the record was last updated (in-memory adapter sets this on each write). */
  readonly updatedAtMonotonicMs: number;
}

export interface StorageAdapter {
  /** Stable identifier of this adapter (e.g. 'memory', 'async-storage'). */
  readonly adapterId: string;

  /** Write a payload under a key. */
  write(key: string, payload: string, options?: StorageWriteOptions): Promise<void>;

  /** Read a payload by key. Returns null when missing. */
  read(key: string): Promise<StorageReadResult>;

  /** Delete a payload by key. No-op when missing. */
  delete(key: string): Promise<void>;

  /** Check whether a payload exists. */
  exists(key: string): Promise<boolean>;

  /** List all keys currently stored. Order is adapter-defined. */
  list(): Promise<readonly string[]>;

  /** Clear every record. Destructive. */
  clear(): Promise<void>;
}
