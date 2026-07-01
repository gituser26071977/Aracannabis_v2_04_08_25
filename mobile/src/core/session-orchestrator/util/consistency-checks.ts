/**
 * consistency-checks — pure projections that compare Runtime and
 * Session state at a point in time and return zero or more
 * InconsistencyReports.
 *
 * Checks (in this order):
 *   1. out-of-order — Runtime event timestamp < last seen monotonic
 *   2. impossible-state — Runtime event requires Session in a state
 *      that cannot legally receive it (e.g. session-resumed when
 *      session is not paused).
 *   3. invalid-cycle — protocol-runtime-cycle-completed cycleIndex
 *      >= plan.cycles
 *   4. invalid-phase — protocol-runtime-phase-changed currentPhase
 *      not in plan.phases
 *   5. divergence — Runtime and Session report terminal states that
 *      are logically incompatible
 */

import type { BreathPhase } from '@araflow/shared-contracts';

import type { SessionState } from '@core/execution-session';
import type { RuntimeEvent, RuntimeState } from '@core/runtime';

import type { InconsistencyReport } from '../domain/InconsistencyReport';
import {
  divergenceReport,
  invalidCycleReport,
  invalidPhaseReport,
  outOfOrderReport,
} from '../domain/InconsistencyReport';

export interface ConsistencyCheckInput {
  readonly runtimeState: RuntimeState;
  readonly sessionState: SessionState;
  readonly event: RuntimeEvent;
  readonly lastSeenMonotonicMs: number;
  readonly totalCycles: number;
  readonly validPhases: readonly BreathPhase[];
}

const sessionCanPause = (s: SessionState): boolean => s === 'running' || s === 'preparing';
const sessionCanResume = (s: SessionState): boolean => s === 'paused';
const sessionCanCancel = (s: SessionState): boolean =>
  s === 'preparing' || s === 'running' || s === 'paused';
const sessionCanComplete = (s: SessionState): boolean => s === 'running';
const sessionCanFail = (s: SessionState): boolean =>
  s === 'preparing' || s === 'running' || s === 'paused';
const sessionCanStart = (s: SessionState): boolean => s === 'idle';

const protocolEventMonotonic = (event: RuntimeEvent): number | null => {
  if (event.source !== 'protocol') {
    return null;
  }
  return event.payload.monotonicMs;
};

export const runConsistencyChecks = (
  input: ConsistencyCheckInput,
): readonly InconsistencyReport[] => {
  const reports: InconsistencyReport[] = [];
  const now = Date.now();
  const evMonotonic = protocolEventMonotonic(input.event);
  if (evMonotonic !== null && evMonotonic < input.lastSeenMonotonicMs) {
    reports.push(
      outOfOrderReport({
        monotonicMs: now,
        eventMonotonicMs: evMonotonic,
        eventType: `${input.event.source}:${String((input.event as { payload?: { type?: unknown } }).payload?.type ?? 'unknown')}`,
      }),
    );
  }

  if (input.event.source === 'protocol') {
    const p = input.event.payload;
    switch (p.type) {
      case 'protocol-runtime-paused':
        if (!sessionCanPause(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted pause while Session cannot legally receive pause',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-paused',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        break;
      case 'protocol-runtime-resumed':
        if (!sessionCanResume(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted resume while Session is not paused',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-resumed',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        break;
      case 'protocol-runtime-completed':
        if (!sessionCanComplete(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted completed while Session is not running',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-completed',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        break;
      case 'protocol-runtime-cycle-completed':
        if (p.cycleIndex >= input.totalCycles && input.totalCycles > 0) {
          reports.push(
            invalidCycleReport({
              monotonicMs: now,
              cycleIndex: p.cycleIndex,
              totalCycles: input.totalCycles,
            }),
          );
        }
        break;
      case 'protocol-runtime-phase-changed':
        if (input.validPhases.length > 0) {
          const cur = p.currentPhase;
          const prev = p.previousPhase;
          if (!(input.validPhases as readonly string[]).includes(cur)) {
            reports.push(invalidPhaseReport({ monotonicMs: now, phase: cur }));
          }
          if (prev !== null && !(input.validPhases as readonly string[]).includes(prev)) {
            reports.push(invalidPhaseReport({ monotonicMs: now, phase: prev }));
          }
        }
        break;
      case 'protocol-runtime-stopped':
        if (p.reason === 'cancelled' && !sessionCanCancel(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted cancelled stop while Session cannot legally receive cancel',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-stopped:cancelled',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        if (p.reason === 'errored' && !sessionCanFail(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted errored stop while Session cannot legally receive fail',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-stopped:errored',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        break;
      case 'protocol-runtime-errored':
        if (!sessionCanFail(input.sessionState)) {
          reports.push(
            Object.freeze({
              kind: 'impossible-state' as const,
              code: 'orchestrator_impossible_state',
              message: 'Runtime emitted errored while Session is already terminal',
              monotonicMs: now,
              context: Object.freeze({
                eventType: 'protocol-runtime-errored',
                sessionState: input.sessionState,
              }),
            }),
          );
        }
        break;
      default:
        break;
    }
  }

  if (
    input.event.source === 'protocol' &&
    input.event.payload.type === 'protocol-runtime-started'
  ) {
    if (!sessionCanStart(input.sessionState)) {
      reports.push(
        Object.freeze({
          kind: 'impossible-state' as const,
          code: 'orchestrator_impossible_state',
          message: 'Runtime emitted started while Session is not idle',
          monotonicMs: now,
          context: Object.freeze({
            eventType: 'protocol-runtime-started',
            sessionState: input.sessionState,
          }),
        }),
      );
    }
  }

  if (input.event.source === 'runtime' && input.event.payload.type === 'runtime-compile-failed') {
    if (input.sessionState !== 'idle') {
      reports.push(
        Object.freeze({
          kind: 'divergence' as const,
          code: 'orchestrator_divergence',
          message: 'Runtime emitted compile-failed while Session is past idle',
          monotonicMs: now,
          context: Object.freeze({
            runtimeState: input.runtimeState,
            sessionState: input.sessionState,
          }),
        }),
      );
    }
  }

  if (input.event.source === 'runtime' && input.event.payload.type === 'runtime-error') {
    if (!sessionCanFail(input.sessionState)) {
      reports.push(
        Object.freeze({
          kind: 'divergence' as const,
          code: 'orchestrator_divergence',
          message: 'Runtime emitted error while Session cannot legally fail',
          monotonicMs: now,
          context: Object.freeze({
            runtimeState: input.runtimeState,
            sessionState: input.sessionState,
          }),
        }),
      );
    } else {
      reports.push(
        divergenceReport({
          monotonicMs: now,
          runtimeState: input.runtimeState,
          sessionState: input.sessionState,
        }),
      );
    }
  }

  return Object.freeze(reports.map((r) => Object.freeze(r)));
};
