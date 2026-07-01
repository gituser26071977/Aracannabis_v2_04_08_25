/**
 * SessionRecording — JSON-serializable export format for a Session's
 * event log. The Recorder captures every event the Session emits and
 * bundles them with identity + metadata into a portable shape.
 *
 * No persistence: the Recording is held in memory and can be passed
 * to `SessionOrchestrator.replay()` to reconstruct a fresh Session.
 *
 * Shape is intentionally flat and JSON-safe so future persistence
 * layers (out of scope for Sprint 6) can serialize it directly.
 */

import type { ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { ExecutionPlanId, SessionEvent } from '@core/execution-session';

export interface SessionRecording {
  readonly version: 1;
  readonly sessionId: SessionId;
  readonly protocolId: ProtocolId;
  readonly executionPlanId: ExecutionPlanId;
  readonly recordedAtMonotonicMs: number;
  readonly eventCount: number;
  readonly events: readonly SessionEvent[];
}

export const RECORDING_VERSION = 1 as const;

export const isSessionRecording = (value: unknown): value is SessionRecording => {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const v = value as Partial<SessionRecording>;
  return (
    v.version === 1 &&
    typeof v.sessionId === 'string' &&
    typeof v.protocolId === 'string' &&
    typeof v.executionPlanId === 'string' &&
    typeof v.recordedAtMonotonicMs === 'number' &&
    typeof v.eventCount === 'number' &&
    Array.isArray(v.events)
  );
};
