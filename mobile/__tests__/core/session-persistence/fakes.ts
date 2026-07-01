/**
 * Test helpers for the session-persistence module.
 *
 * Builds a real ExecutionSession from a small fake plan, then exposes
 * helpers to capture snapshots, run lifecycle transitions, etc.
 */

import { type ProtocolId, type SessionId } from '@araflow/shared-contracts';

import { ExecutionSession, ExecutionPlanId } from '@core/execution-session';

import { fakePlan } from '../session-orchestrator/fake-plan';

export const SESSION_ID = '01ARZ3NDEKTSV4RRFFQ69G5F01' as SessionId;
export const PROTOCOL_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV' as ProtocolId;
export const EXECUTION_PLAN_ID = ExecutionPlanId('01HXYZ00000000000000000000');

export interface FakeSessionOptions {
  readonly now?: () => number;
  readonly planCycles?: number;
}

export const buildFakeSession = (options: FakeSessionOptions = {}): ExecutionSession => {
  const now = options.now ?? ((): number => 0);
  return new ExecutionSession({
    sessionId: SESSION_ID,
    protocolId: PROTOCOL_ID,
    executionPlanId: EXECUTION_PLAN_ID,
    plan: fakePlan(options.planCycles ?? 2),
    now,
  });
};

/** Advance the session into the running state for richer snapshots. */
export const startSession = (
  session: ExecutionSession,
  now: () => number = (): number => 0,
): void => {
  session.start();
  // simulate a phase change to add events to the log
  session.recordPhaseChange({
    phase: 'inhaling',
    cycleIndex: 0,
    phaseIndex: 0,
    phaseElapsedMs: 0,
    phaseDurationMs: 1000,
    monotonicMs: now(),
  });
};
