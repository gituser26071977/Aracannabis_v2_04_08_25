/**
 * session-to-snapshot — pure projection from an ExecutionSession to a
 * PersistedSessionSnapshot.
 *
 * Keeps the Aggregate unchanged: the persistence layer doesn't poke
 * at internal state, it reads the public read models.
 */

import type { ExecutionSession, SessionState } from '@core/execution-session';
import { TERMINAL_SESSION_STATES } from '@core/execution-session';

import type { PersistedSessionSnapshot } from '../domain/SessionSnapshot';
import type { SnapshotLifecycleStage } from '../domain/SnapshotMetadata';
import { buildSnapshotMetadata } from '../domain/SnapshotMetadata';

export interface SessionToSnapshotInput {
  readonly session: ExecutionSession;
  /** Optional pre-generated snapshot id. Defaults to a deterministic id. */
  readonly snapshotId?: string;
  /** Capture time (monotonic). */
  readonly capturedAtMonotonicMs: number;
  /** Serializer schema version (pinned at capture time). */
  readonly serializerVersion: number;
  /** Optional label. */
  readonly label?: string;
}

const isTerminal = (state: SessionState): boolean =>
  (TERMINAL_SESSION_STATES as readonly SessionState[]).includes(state);

const stageFor = (state: SessionState): SnapshotLifecycleStage =>
  isTerminal(state) ? 'terminal' : 'in-flight';

const defaultSnapshotId = (input: SessionToSnapshotInput): string => {
  // Deterministic id — same session + capture time → same id.
  // The capture time differs across snapshots, so this naturally
  // produces a new id per save.
  return `snap_${input.session.sessionId()}_${String(input.capturedAtMonotonicMs)}`;
};

export const sessionToPersistedSnapshot = (
  input: SessionToSnapshotInput,
): PersistedSessionSnapshot => {
  const session = input.session;
  const state = session.state();
  const metadataInput = {
    snapshotId: input.snapshotId ?? defaultSnapshotId(input),
    sessionId: session.sessionId(),
    protocolId: session.protocolId(),
    executionPlanId: session.executionPlanId(),
    stage: stageFor(state),
    capturedAtMonotonicMs: input.capturedAtMonotonicMs,
    updatedAtMonotonicMs: input.capturedAtMonotonicMs,
    serializerVersion: input.serializerVersion,
    ...(input.label === undefined ? {} : { label: input.label }),
  };
  return Object.freeze({
    metadata: buildSnapshotMetadata(metadataInput),
    state,
    metrics: session.metrics(),
    timeline: session.timeline(),
    events: session.events(),
    plan: session.plan(),
  });
};
