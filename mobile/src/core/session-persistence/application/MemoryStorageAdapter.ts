/**
 * MemoryStorageAdapter — in-memory implementation of StorageAdapter.
 *
 * Per Sprint 7 brief: the only storage adapter in scope is in-memory.
 * No AsyncStorage, no SQLite, no filesystem.
 *
 * Each entry records a monotonic timestamp at write time. The clock
 * is injectable for tests.
 */

import type {
  StorageAdapter,
  StorageReadResult,
  StorageWriteOptions,
} from '../domain/StorageAdapter';

export const MEMORY_STORAGE_ADAPTER_ID = 'memory' as const;

export interface MemoryStorageAdapterOptions {
  /** Monotonic clock used to stamp writes. Defaults to `Date.now`-style fallback. */
  readonly now?: () => number;
}

interface MemoryEntry {
  readonly payload: string;
  readonly updatedAtMonotonicMs: number;
}

export const createMemoryStorageAdapter = (
  options: MemoryStorageAdapterOptions = {},
): StorageAdapter => {
  const clock = options.now ?? ((): number => Date.now());
  const store = new Map<string, MemoryEntry>();

  const bump = (key: string, payload: string): MemoryEntry => {
    const entry: MemoryEntry = { payload, updatedAtMonotonicMs: clock() };
    store.set(key, entry);
    return entry;
  };

  return {
    adapterId: MEMORY_STORAGE_ADAPTER_ID,

    async write(key: string, payload: string, writeOptions?: StorageWriteOptions): Promise<void> {
      const overwrite = writeOptions?.overwrite ?? true;
      if (!overwrite && store.has(key)) {
        throw new Error(`MemoryStorageAdapter.write: key "${key}" already exists`);
      }
      bump(key, payload);
    },

    async read(key: string): Promise<StorageReadResult> {
      const entry = store.get(key);
      if (entry === undefined) {
        return { payload: null, updatedAtMonotonicMs: clock() };
      }
      return { payload: entry.payload, updatedAtMonotonicMs: entry.updatedAtMonotonicMs };
    },

    async delete(key: string): Promise<void> {
      store.delete(key);
    },

    async exists(key: string): Promise<boolean> {
      return store.has(key);
    },

    async list(): Promise<readonly string[]> {
      return Array.from(store.keys());
    },

    async clear(): Promise<void> {
      store.clear();
    },
  };
};
