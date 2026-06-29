/**
 * ExecutionSessionDeps — constructor options for `ExecutionSession`.
 *
 * The Aggregate is a pure domain object. It owns:
 *   - Its immutable identity (SessionId, ProtocolId, ExecutionPlanId)
 *   - A frozen reference to the ExecutionPlan (never mutated)
 *   - A monotonic clock function (provided by caller — defaults to
 *     `Date.now` if not supplied, but tests typically inject a fake)
 *
 * Callers MUST NOT inject state. The session builds its own state
 * from its event log.
 */

import type { ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

import type { ExecutionPlanId } from '../domain/SessionEvent';

export type MonotonicClock = () => number;

export interface ExecutionSessionDeps {
  /** Required — branded session id (ULID). */
  readonly sessionId: SessionId;

  /** Required — branded protocol id (ULID). */
  readonly protocolId: ProtocolId;

  /** Required — opaque plan id (typically plan.executionId). */
  readonly executionPlanId: ExecutionPlanId;

  /** Required — frozen plan reference; the Aggregate stores but never mutates it. */
  readonly plan: ProtocolExecutionPlan;

  /**
   * Optional monotonic clock. If omitted, `Date.now` is used. Tests
   * inject a controllable clock to drive deterministic time.
   */
  readonly now?: MonotonicClock;
}
