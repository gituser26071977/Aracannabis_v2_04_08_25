/**
 * SessionSnapshot (persistence flavor) — the full payload persisted
 * to a StorageAdapter.
 *
 * This is distinct from `@core/execution-session`'s `SessionSnapshot`,
 * which is a live point-in-time projection produced by the Aggregate.
 * The persistence flavor captures everything needed to reconstruct
 * the Session state offline: metadata + state + metrics + timeline +
 * event log + plan.
 *
 * Distinct types keep the Aggregate Root unchanged. The mapping from
 * ExecutionSession → PersistedSessionSnapshot lives in
 * `util/session-to-snapshot.ts`.
 */

import type {
  SessionEvent,
  SessionMetrics,
  SessionState,
  SessionTimeline,
} from '@core/execution-session';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

import type { SnapshotMetadata } from './SnapshotMetadata';

/**
 * Full persisted snapshot. All fields are required — partial snapshots
 * are not supported (callers can ignore timeline/events if they don't
 * need them, but the wire shape always carries everything).
 */
export interface PersistedSessionSnapshot {
  readonly metadata: SnapshotMetadata;
  readonly state: SessionState;
  readonly metrics: SessionMetrics;
  readonly timeline: SessionTimeline;
  readonly events: readonly SessionEvent[];
  readonly plan: ProtocolExecutionPlan;
}

/**
 * Internal storage record. Wraps the snapshot with an opaque blob
 * produced by a serializer. The shape is intentionally thin: one
 * envelope with a typed `format` discriminator and a `payload` (already
 * encoded by the serializer).
 *
 * Adapters store the entire envelope as an opaque string.
 */
export interface StorageRecord {
  readonly format: 'araflow.session-snapshot';
  readonly schemaVersion: number;
  readonly sessionId: string;
  readonly payload: string;
}

/** Type guard. */
export const isStorageRecord = (v: unknown): v is StorageRecord => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const r = v as Partial<StorageRecord>;
  return (
    r.format === 'araflow.session-snapshot' &&
    typeof r.schemaVersion === 'number' &&
    typeof r.sessionId === 'string' &&
    typeof r.payload === 'string'
  );
};
