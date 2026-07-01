/**
 * @core/session-persistence — local-only persistence layer for the
 * AraFlow Session Orchestrator.
 *
 * Provides:
 *   - a versioned serializer (deterministic JSON)
 *   - an abstract StorageAdapter (in-memory implementation in scope)
 *   - a PersistenceService that wires serializer + storage + migrations
 *   - a Recovery API (canRecover / recover / discard) — explicit only
 *
 * Constraints (per Sprint 7 brief):
 *   - local-only; no backend, no cloud, no sync
 *   - no AsyncStorage / SQLite / filesystem in this sprint
 *   - orchestrator remains decoupled; it does not import this module
 *
 * Version: 1.0.0
 */

// --- Domain ---
export {
  type SnapshotMetadata,
  type SnapshotLifecycleStage,
  buildSnapshotMetadata,
  isSnapshotMetadata,
  isSnapshotLifecycleStage,
} from './domain/SnapshotMetadata';
export {
  type PersistedSessionSnapshot,
  type StorageRecord,
  isStorageRecord,
} from './domain/SessionSnapshot';
export {
  type StorageAdapter,
  type StorageReadResult,
  type StorageWriteOptions,
} from './domain/StorageAdapter';
export {
  type SessionSerializer,
  type SessionDecoder,
  type SerializedSnapshot,
  SERIALIZER_SCHEMA_VERSION,
} from './domain/SessionSerializer';
export {
  type RecoveryProbe,
  type RecoveryResult,
  type RecoveryReason,
  isRecoveryProbe,
} from './domain/RecoveryDecision';
export {
  type SessionPersistence,
  type SaveInput,
  type SaveResult,
  type LoadResult,
  type SaveFailureReason,
  type LoadFailureReason,
} from './domain/SessionPersistence';

// --- Application ---
export { createJsonSerializer, JSON_SERIALIZER_ID } from './application/JsonSerializer';
export {
  createMemoryStorageAdapter,
  MEMORY_STORAGE_ADAPTER_ID,
} from './application/MemoryStorageAdapter';
export {
  createPersistenceService,
  PERSISTENCE_SERVICE_ID,
  CURRENT_SCHEMA_VERSION,
  type PersistenceServiceDeps,
} from './application/PersistenceService';
export { createMigrationRegistry, type MigrationRegistry } from './application/MigrationRegistry';
export {
  createRecoveryAPI,
  RECOVERY_API_ID,
  type RecoveryAPIDeps,
  type RecoveryAPI,
} from './application/RecoveryAPI';

// --- Utilities ---
export { stringifyDeterministic, parseDeterministic } from './util/deterministic-json';
export {
  sessionToPersistedSnapshot,
  type SessionToSnapshotInput,
} from './util/session-to-snapshot';

// --- Version ---
export const SESSION_PERSISTENCE_VERSION = '1.0.0' as const;
