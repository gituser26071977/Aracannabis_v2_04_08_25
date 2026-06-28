/**
 * Persistence — SqliteDatabase interface only.
 *
 * Implementation: WatermelonDB (preferred) or expo-sqlite.
 */

export type SqlParam = string | number | boolean | null | Uint8Array;

export interface SqliteDatabase {
  execute(sql: string, params?: readonly SqlParam[]): Promise<{ rowsAffected: number }>;
  query<T = unknown>(sql: string, params?: readonly SqlParam[]): Promise<readonly T[]>;
  queryOne<T = unknown>(sql: string, params?: readonly SqlParam[]): Promise<T | null>;
  transaction<T>(fn: (tx: SqliteTransaction) => Promise<T>): Promise<T>;
}

export interface SqliteTransaction {
  execute(sql: string, params?: readonly SqlParam[]): Promise<{ rowsAffected: number }>;
  query<T = unknown>(sql: string, params?: readonly SqlParam[]): Promise<readonly T[]>;
  queryOne<T = unknown>(sql: string, params?: readonly SqlParam[]): Promise<T | null>;
}
