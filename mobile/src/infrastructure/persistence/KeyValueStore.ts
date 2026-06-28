/**
 * Persistence — KeyValueStore interface only.
 *
 * Implementação concreta (AsyncStorage, MMKV, WatermelonDB) será
 * plugada em sprint subsequente.
 */

export interface KeyValueStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
  multiGet(keys: readonly string[]): Promise<readonly (readonly [string, string | null])[]>;
  multiSet(entries: readonly (readonly [string, string])[]): Promise<void>;
  multiRemove(keys: readonly string[]): Promise<void>;
}
