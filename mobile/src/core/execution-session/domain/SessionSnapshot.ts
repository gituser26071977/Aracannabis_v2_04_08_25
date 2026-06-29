/**
 * SessionSnapshot — immutable point-in-time capture of a session.
 *
 * Snapshots are produced by `ExecutionSession.snapshot()` and carry
 * a monotonically increasing `version` (incremented on every state
 * change). Consumers can use the version to detect stale reads.
 */

import type { BreathPhase, ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { ExecutionPlanId } from './SessionEvent';
import type { SessionMetrics } from './SessionMetrics';
import type { SessionState } from './SessionState';

export interface SessionSnapshot {
  readonly sessionId: SessionId;
  readonly protocolId: ProtocolId;
  readonly executionPlanId: ExecutionPlanId;
  readonly state: SessionState;
  readonly elapsedMs: number;
  readonly remainingMs: number;
  readonly currentPhase: BreathPhase | null;
  readonly currentCycle: number;
  readonly progress: number;
  readonly metrics: SessionMetrics;
  readonly timestamp: number;
  readonly version: number;
}
