/**
 * SnapshotMetadata — header for a persisted Session snapshot.
 *
 * Carries identity, timestamps, and serializer version. The metadata
 * is the only field checked before the (potentially expensive)
 * payload is decoded. A malformed `version` is enough to reject the
 * snapshot without inspecting the payload.
 *
 * No app-level state is leaked into metadata. Only identifiers,
 * timestamps, and serializer metadata are stored.
 */

import type { ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { ExecutionPlanId } from '@core/execution-session';

/** Discriminator describing the lifecycle stage at capture time. */
export type SnapshotLifecycleStage = 'in-flight' | 'terminal';

export interface SnapshotMetadata {
  /** Stable identifier of this specific snapshot (UUID-like). */
  readonly snapshotId: string;
  /** Session this snapshot belongs to. */
  readonly sessionId: SessionId;
  /** Protocol used by the session. */
  readonly protocolId: ProtocolId;
  /** Compiled execution plan used by the session. */
  readonly executionPlanId: ExecutionPlanId;
  /** Snapshot lifecycle stage. */
  readonly stage: SnapshotLifecycleStage;
  /** Capture time in milliseconds from a monotonic clock. */
  readonly capturedAtMonotonicMs: number;
  /** Last update time (re-saves bump this without changing snapshotId). */
  readonly updatedAtMonotonicMs: number;
  /** Serializer schema version. Bump on breaking payload changes. */
  readonly serializerVersion: number;
  /** Optional human-readable label. */
  readonly label?: string;
}

/** Build a minimal metadata record with sensible defaults. */
export const buildSnapshotMetadata = (input: {
  readonly snapshotId: string;
  readonly sessionId: SessionId;
  readonly protocolId: ProtocolId;
  readonly executionPlanId: ExecutionPlanId;
  readonly stage: SnapshotLifecycleStage;
  readonly capturedAtMonotonicMs: number;
  readonly updatedAtMonotonicMs: number;
  readonly serializerVersion: number;
  readonly label?: string;
}): SnapshotMetadata => {
  const base: SnapshotMetadata = Object.freeze({
    snapshotId: input.snapshotId,
    sessionId: input.sessionId,
    protocolId: input.protocolId,
    executionPlanId: input.executionPlanId,
    stage: input.stage,
    capturedAtMonotonicMs: input.capturedAtMonotonicMs,
    updatedAtMonotonicMs: input.updatedAtMonotonicMs,
    serializerVersion: input.serializerVersion,
  });
  return input.label === undefined ? base : Object.freeze({ ...base, label: input.label });
};

/** Type guard. */
export const isSnapshotLifecycleStage = (v: unknown): v is SnapshotLifecycleStage =>
  v === 'in-flight' || v === 'terminal';

/** Type guard for SnapshotMetadata (lightweight). */
export const isSnapshotMetadata = (v: unknown): v is SnapshotMetadata => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const m = v as Partial<SnapshotMetadata>;
  return (
    typeof m.snapshotId === 'string' &&
    typeof m.sessionId === 'string' &&
    typeof m.protocolId === 'string' &&
    typeof m.executionPlanId === 'string' &&
    isSnapshotLifecycleStage(m.stage) &&
    typeof m.capturedAtMonotonicMs === 'number' &&
    typeof m.updatedAtMonotonicMs === 'number' &&
    typeof m.serializerVersion === 'number'
  );
};
