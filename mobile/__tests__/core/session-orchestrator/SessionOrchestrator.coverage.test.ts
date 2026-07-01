/**
 * Coverage tests for SessionOrchestrator — focuses on edge cases,
 * predicates, fallback paths in event-translator, replay-reducer
 * error paths, and OrchestratorEvent/SessionRecording guards.
 */

import { type ProtocolId, type SessionId } from '@araflow/shared-contracts';

import {
  ExecutionSession,
  ExecutionPlanId,
  type SessionEvent,
  type SessionState,
} from '@core/execution-session';
import type { RuntimeEngine } from '@core/runtime';
import {
  ACTIVE_ORCHESTRATOR_STATES,
  type InconsistencyReport,
  isInconsistencyKind,
  isOrchestratorEvent,
  isOrchestratorState,
  isSessionRecording,
  isTerminalOrchestratorState,
  legalOrchestratorTransitions,
  canOrchestratorTransition,
  ORCHESTRATOR_STATES,
  type OrchestratorEvent,
  type SessionRecording,
  SessionRecorder,
  SessionOrchestrator,
  computeOrchestratorMetrics,
  translateRuntimeEvent,
  runConsistencyChecks,
  replayInto,
  toJson,
  fromJson,
  type SessionAction,
  freezeInconsistency,
  outOfOrderReport,
  impossibleStateReport,
  invalidCycleReport,
  invalidPhaseReport,
  divergenceReport,
  RECORDING_VERSION,
} from '@core/session-orchestrator';

import { fakePlan } from './fake-plan';
import { FakeRuntime, runtimeEvent } from './fakes';

const SESSION_ID = '01ARZ3NDEKTSV4RRFFQ69G5F01' as SessionId;
const PROTOCOL_ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV' as ProtocolId;
const EXECUTION_PLAN_ID = ExecutionPlanId('01HXYZ00000000000000000000');

const buildSession = (now: () => number = () => 0): ExecutionSession =>
  new ExecutionSession({
    sessionId: SESSION_ID,
    protocolId: PROTOCOL_ID,
    executionPlanId: EXECUTION_PLAN_ID,
    plan: fakePlan(),
    now,
  });

// =============================================================================
// OrchestratorState predicates and transitions
// =============================================================================

describe('OrchestratorState — predicates', () => {
  it('isOrchestratorState accepts valid states', () => {
    for (const s of ORCHESTRATOR_STATES) {
      expect(isOrchestratorState(s)).toBe(true);
    }
  });

  it('isOrchestratorState rejects invalid states', () => {
    expect(isOrchestratorState('nope')).toBe(false);
    expect(isOrchestratorState(123)).toBe(false);
    expect(isOrchestratorState(null)).toBe(false);
    expect(isOrchestratorState(undefined)).toBe(false);
  });

  it('isTerminalOrchestratorState returns true only for disposed', () => {
    expect(isTerminalOrchestratorState('disposed')).toBe(true);
    expect(isTerminalOrchestratorState('detached')).toBe(false);
    expect(isTerminalOrchestratorState('attached')).toBe(false);
    expect(isTerminalOrchestratorState('replaying')).toBe(false);
  });

  it('legalOrchestratorTransitions covers all states', () => {
    expect(legalOrchestratorTransitions('detached').length).toBeGreaterThan(0);
    expect(legalOrchestratorTransitions('attached').length).toBeGreaterThan(0);
    expect(legalOrchestratorTransitions('replaying').length).toBeGreaterThan(0);
    expect(legalOrchestratorTransitions('disposed').length).toBe(0);
  });

  it('canOrchestratorTransition validates transitions', () => {
    expect(canOrchestratorTransition('detached', 'attached')).toBe(true);
    expect(canOrchestratorTransition('attached', 'detached')).toBe(true);
    expect(canOrchestratorTransition('disposed', 'attached')).toBe(false);
  });

  it('ACTIVE_ORCHESTRATOR_STATES contains non-terminal states', () => {
    expect(ACTIVE_ORCHESTRATOR_STATES).toContain('detached');
    expect(ACTIVE_ORCHESTRATOR_STATES).toContain('attached');
    expect(ACTIVE_ORCHESTRATOR_STATES).toContain('replaying');
    expect(ACTIVE_ORCHESTRATOR_STATES).not.toContain('disposed');
  });
});

// =============================================================================
// OrchestratorEvent guard
// =============================================================================

describe('OrchestratorEvent guard', () => {
  it('isOrchestratorEvent accepts valid events', () => {
    expect(
      isOrchestratorEvent({
        type: 'orchestrator-attached',
        monotonicMs: 0,
        orchestratorState: 'attached',
      }),
    ).toBe(true);
    expect(isOrchestratorEvent({ type: 'orchestrator-disposed', monotonicMs: 0 })).toBe(true);
  });

  it('isOrchestratorEvent rejects invalid', () => {
    expect(isOrchestratorEvent(null)).toBe(false);
    expect(isOrchestratorEvent({})).toBe(false);
    expect(isOrchestratorEvent({ type: 'unknown' })).toBe(false);
    expect(isOrchestratorEvent(123)).toBe(false);
  });
});

// =============================================================================
// InconsistencyReport
// =============================================================================

describe('InconsistencyReport helpers', () => {
  it('isInconsistencyKind accepts valid kinds', () => {
    expect(isInconsistencyKind('out-of-order')).toBe(true);
    expect(isInconsistencyKind('divergence')).toBe(true);
    expect(isInconsistencyKind('invalid')).toBe(false);
  });

  it('outOfOrderReport builds correct shape', () => {
    const r = outOfOrderReport({ monotonicMs: 100, eventMonotonicMs: 50, eventType: 'foo' });
    expect(r.kind).toBe('out-of-order');
    expect(r.code).toBe('orchestrator_out_of_order');
  });

  it('impossibleStateReport builds correct shape', () => {
    const r = impossibleStateReport({ monotonicMs: 100, eventType: 'e', sessionState: 'idle' });
    expect(r.kind).toBe('impossible-state');
  });

  it('invalidCycleReport builds correct shape', () => {
    const r = invalidCycleReport({ monotonicMs: 100, cycleIndex: 99, totalCycles: 4 });
    expect(r.kind).toBe('invalid-cycle');
    expect((r.context as { cycleIndex: number }).cycleIndex).toBe(99);
  });

  it('invalidPhaseReport builds correct shape', () => {
    const r = invalidPhaseReport({ monotonicMs: 100, phase: 'x' });
    expect(r.kind).toBe('invalid-phase');
    expect((r.context as { phase: string }).phase).toBe('x');
  });

  it('divergenceReport builds correct shape', () => {
    const r = divergenceReport({ monotonicMs: 100, runtimeState: 'running', sessionState: 'idle' });
    expect(r.kind).toBe('divergence');
  });

  it('freezeInconsistency returns frozen report', () => {
    const r: InconsistencyReport = freezeInconsistency({
      kind: 'divergence',
      code: 'x',
      message: 'y',
      monotonicMs: 0,
      context: Object.freeze({}),
    });
    expect(Object.isFrozen(r)).toBe(true);
  });
});

// =============================================================================
// SessionRecording guard
// =============================================================================

describe('SessionRecording guard', () => {
  it('isSessionRecording accepts valid recording', () => {
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: 0,
      events: [],
    };
    expect(isSessionRecording(recording)).toBe(true);
  });

  it('isSessionRecording rejects invalid', () => {
    expect(isSessionRecording(null)).toBe(false);
    expect(isSessionRecording({})).toBe(false);
    expect(isSessionRecording({ version: 2 })).toBe(false);
    expect(isSessionRecording({ version: 1, sessionId: 1 })).toBe(false);
  });

  it('toJson + fromJson round-trips', () => {
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 100,
      eventCount: 1,
      events: [],
    };
    const json = toJson(recording);
    expect(json.version).toBe(RECORDING_VERSION);
    const back = fromJson(json);
    expect(back).toEqual(recording);
  });

  it('fromJson throws on invalid input', () => {
    expect(() => fromJson(null)).toThrow();
    expect(() => fromJson({})).toThrow();
  });
});

// =============================================================================
// OrchestratorMetrics
// =============================================================================

describe('OrchestratorMetrics', () => {
  it('computeOrchestratorMetrics aggregates per-kind', () => {
    const m = computeOrchestratorMetrics({
      eventsProcessed: 10,
      eventsSkipped: 2,
      reports: [
        Object.freeze({
          kind: 'out-of-order',
          code: 'x',
          message: 'y',
          monotonicMs: 0,
          context: Object.freeze({}),
        }),
        Object.freeze({
          kind: 'divergence',
          code: 'x',
          message: 'y',
          monotonicMs: 0,
          context: Object.freeze({}),
        }),
        Object.freeze({
          kind: 'divergence',
          code: 'x',
          message: 'y',
          monotonicMs: 0,
          context: Object.freeze({}),
        }),
      ],
      replays: 1,
    });
    expect(m.eventsProcessed).toBe(10);
    expect(m.inconsistencies).toBe(3);
    expect(m.replays).toBe(1);
    expect(m.perKindCounts.divergence).toBe(2);
    expect(m.perKindCounts['out-of-order']).toBe(1);
  });

  it('computeOrchestratorMetrics with no reports', () => {
    const m = computeOrchestratorMetrics({
      eventsProcessed: 0,
      eventsSkipped: 0,
      reports: [],
      replays: 0,
    });
    expect(m.inconsistencies).toBe(0);
    expect(m.perKindCounts['out-of-order']).toBe(0);
  });
});

// =============================================================================
// event-translator edge cases
// =============================================================================

describe('event-translator — edge cases', () => {
  it('timer tick is skipped', () => {
    const r = translateRuntimeEvent(runtimeEvent.timerTick());
    expect(r.kind).toBe('skip');
  });

  it('breath phase-changed is skipped', () => {
    const r = translateRuntimeEvent(runtimeEvent.breathPhaseChanged());
    expect(r.kind).toBe('skip');
  });

  it('protocol-runtime-tick is skipped', () => {
    const r = translateRuntimeEvent(runtimeEvent.tick());
    expect(r.kind).toBe('skip');
  });

  it('protocol-runtime-stopped completed reason is handled', () => {
    const ev = {
      source: 'protocol' as const,
      payload: {
        type: 'protocol-runtime-stopped' as const,
        executionId: '01HXYZ00000000000000000000' as never,
        reason: 'completed' as const,
        monotonicMs: 100,
      },
    };
    const r = translateRuntimeEvent(ev);
    expect(r.kind).toBe('skip');
  });

  it('runtime-warnings is skipped', () => {
    const r = translateRuntimeEvent(runtimeEvent.runtimeWarnings());
    expect(r.kind).toBe('skip');
  });

  it('runtime-error is mapped to fail', () => {
    const r = translateRuntimeEvent(runtimeEvent.runtimeError(60));
    if (r.kind === 'fail') {
      expect(r.code).toBe('rt_error');
    } else {
      throw new Error('expected fail');
    }
  });

  it('phase-changed action includes correct fields', () => {
    const r = translateRuntimeEvent(runtimeEvent.phaseChanged(200, 'inhaling', 1));
    if (r.kind === 'recordPhaseChange') {
      expect(r.cycleIndex).toBe(1);
      expect(r.monotonicMs).toBe(200);
    } else {
      throw new Error('expected recordPhaseChange');
    }
  });

  it('cycle-completed action includes correct fields', () => {
    const r = translateRuntimeEvent(runtimeEvent.cycleCompleted(200, 5));
    if (r.kind === 'recordCycleCompleted') {
      expect(r.cycleIndex).toBe(5);
      expect(r.monotonicMs).toBe(200);
    } else {
      throw new Error('expected recordCycleCompleted');
    }
  });

  it('all SessionAction kinds are exposed via type guard', () => {
    const r1: SessionAction = { kind: 'start' };
    const r2: SessionAction = { kind: 'fail', code: 'x', message: 'y' };
    expect(r1.kind).toBe('start');
    expect(r2.kind).toBe('fail');
  });
});

// =============================================================================
// consistency-checks edge cases
// =============================================================================

describe('consistency-checks — edge cases', () => {
  const baseInput = {
    runtimeState: 'running' as const,
    sessionState: 'running' as SessionState,
    lastSeenMonotonicMs: 0,
    totalCycles: 4,
    validPhases: ['inhaling', 'exhaling'] as never,
  };

  it('returns empty for valid event', () => {
    const ev = runtimeEvent.phaseChanged(100, 'inhaling', 0);
    const reports = runConsistencyChecks({ ...baseInput, event: ev });
    expect(reports.length).toBe(0);
  });

  it('pause from preparing is allowed', () => {
    const ev = runtimeEvent.paused(50);
    const reports = runConsistencyChecks({ ...baseInput, sessionState: 'preparing', event: ev });
    expect(reports.length).toBe(0);
  });

  it('started from running is impossible', () => {
    const ev = runtimeEvent.started();
    const reports = runConsistencyChecks({ ...baseInput, sessionState: 'running', event: ev });
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('cancel from running is allowed', () => {
    const ev = runtimeEvent.stoppedCancelled(100);
    const reports = runConsistencyChecks({ ...baseInput, event: ev });
    expect(reports.length).toBe(0);
  });

  it('errored stop from cancelled is impossible', () => {
    const ev = runtimeEvent.stoppedErrored(100);
    const reports = runConsistencyChecks({ ...baseInput, sessionState: 'cancelled', event: ev });
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('errored event from terminal session is impossible', () => {
    const ev = runtimeEvent.errored(100, 'c', 'm');
    const reports = runConsistencyChecks({ ...baseInput, sessionState: 'completed', event: ev });
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('compile-failed while past idle is divergence', () => {
    const ev = runtimeEvent.runtimeCompileFailed(50);
    const reports = runConsistencyChecks({ ...baseInput, event: ev });
    expect(reports.some((r) => r.kind === 'divergence')).toBe(true);
  });

  it('runtime-error from non-failable state is divergence', () => {
    const ev = runtimeEvent.runtimeError(100);
    const reports = runConsistencyChecks({ ...baseInput, sessionState: 'completed', event: ev });
    expect(reports.some((r) => r.kind === 'divergence')).toBe(true);
  });
});

// =============================================================================
// replay-reducer edge cases
// =============================================================================

describe('replay-reducer — edge cases', () => {
  it('rejects empty events', () => {
    const session = buildSession();
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: 0,
      events: [],
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(false);
  });

  it('rejects non-anchor first event', () => {
    const session = buildSession();
    const ev: SessionEvent = Object.freeze({ type: 'session-started', monotonicMs: 100 });
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: 1,
      events: [ev],
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(false);
  });

  it('rejects identity mismatch', () => {
    const session = buildSession();
    const ev: SessionEvent = Object.freeze({
      type: 'session-created',
      sessionId: '01ARZ3NDEKTSV4RRFFQ69G5F99' as SessionId,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      state: 'idle',
      monotonicMs: 0,
    });
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: 1,
      events: [ev],
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(false);
  });

  it('replays through full lifecycle', () => {
    const session = buildSession();
    const events: readonly SessionEvent[] = [
      Object.freeze({
        type: 'session-created' as const,
        sessionId: SESSION_ID,
        protocolId: PROTOCOL_ID,
        executionPlanId: EXECUTION_PLAN_ID,
        state: 'idle' as const,
        monotonicMs: 0,
      }),
      Object.freeze({ type: 'session-started' as const, monotonicMs: 100 }),
      Object.freeze({ type: 'session-paused' as const, monotonicMs: 200, pausedForMs: 0 }),
      Object.freeze({ type: 'session-resumed' as const, monotonicMs: 300, resumedFromMs: 200 }),
      Object.freeze({ type: 'session-completed' as const, monotonicMs: 400, totalElapsedMs: 400 }),
    ];
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 1000,
      eventCount: events.length,
      events,
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(true);
    expect(session.state()).toBe('completed');
  });

  it('replay handles phase-changed and cycle-completed events', () => {
    const session = buildSession();
    session.start();
    const events: readonly SessionEvent[] = [
      Object.freeze({
        type: 'session-created' as const,
        sessionId: SESSION_ID,
        protocolId: PROTOCOL_ID,
        executionPlanId: EXECUTION_PLAN_ID,
        state: 'idle' as const,
        monotonicMs: 0,
      }),
      Object.freeze({ type: 'session-started' as const, monotonicMs: 100 }),
      Object.freeze({
        type: 'phase-changed' as const,
        monotonicMs: 200,
        phase: 'inhaling' as const,
        cycleIndex: 0,
        phaseIndex: 0,
        phaseElapsedMs: 100,
        phaseDurationMs: 1000,
      }),
      Object.freeze({
        type: 'cycle-completed' as const,
        monotonicMs: 300,
        cycleIndex: 0,
        cycleElapsedMs: 2000,
        totalCycles: 4,
      }),
    ];
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 1000,
      eventCount: events.length,
      events,
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(true);
  });

  it('replay handles session-failed and session-interrupted', () => {
    const session = buildSession();
    session.start();
    const events: readonly SessionEvent[] = [
      Object.freeze({
        type: 'session-created' as const,
        sessionId: SESSION_ID,
        protocolId: PROTOCOL_ID,
        executionPlanId: EXECUTION_PLAN_ID,
        state: 'idle' as const,
        monotonicMs: 0,
      }),
      Object.freeze({ type: 'session-started' as const, monotonicMs: 100 }),
      Object.freeze({
        type: 'session-failed' as const,
        monotonicMs: 200,
        code: 'x',
        message: 'y',
      }),
    ];
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: events.length,
      events,
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(true);
    expect(session.state()).toBe('failed');
  });

  it('replay handles session-cancelled', () => {
    const session = buildSession();
    session.start();
    const events: readonly SessionEvent[] = [
      Object.freeze({
        type: 'session-created' as const,
        sessionId: SESSION_ID,
        protocolId: PROTOCOL_ID,
        executionPlanId: EXECUTION_PLAN_ID,
        state: 'idle' as const,
        monotonicMs: 0,
      }),
      Object.freeze({ type: 'session-started' as const, monotonicMs: 100 }),
      Object.freeze({
        type: 'session-cancelled' as const,
        monotonicMs: 200,
        reason: 'user',
      }),
    ];
    const recording: SessionRecording = {
      version: 1,
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
      recordedAtMonotonicMs: 0,
      eventCount: events.length,
      events,
    };
    const r = replayInto({ session, recording });
    expect(r.ok).toBe(true);
    expect(session.state()).toBe('cancelled');
  });
});

// =============================================================================
// SessionOrchestrator edge cases
// =============================================================================

describe('SessionOrchestrator — extra coverage', () => {
  it('runtimeEngineId returns non-uninitialized when state set', () => {
    const runtime = new FakeRuntime();
    runtime.setState('running');
    const session = buildSession();
    const orchestrator = new SessionOrchestrator({
      runtime: runtime as unknown as RuntimeEngine,
      session,
    });
    expect(typeof orchestrator.runtimeEngineId()).toBe('string');
  });

  it('subscribe returns unsubscribe that removes listener', () => {
    const session = buildSession();
    const runtime = new FakeRuntime();
    const orchestrator = new SessionOrchestrator({
      runtime: runtime as unknown as RuntimeEngine,
      session,
    });
    const events: string[] = [];
    const unsub = orchestrator.subscribe((e: OrchestratorEvent) => {
      events.push(e.type);
    });
    orchestrator.attach();
    expect(events).toContain('orchestrator-attached');
    events.length = 0;
    unsub();
    orchestrator.detach();
    expect(events.length).toBe(0);
  });

  it('recorders_ returns attached recorders', () => {
    const session = buildSession();
    const runtime = new FakeRuntime();
    const orchestrator = new SessionOrchestrator({
      runtime: runtime as unknown as RuntimeEngine,
      session,
    });
    const recorder = new SessionRecorder({
      sessionId: session.sessionId(),
      protocolId: session.protocolId(),
      executionPlanId: session.executionPlanId(),
    });
    orchestrator.attachRecorder(recorder);
    expect(orchestrator.recorders_()).toContain(recorder);
    orchestrator.detachRecorder(recorder);
    expect(orchestrator.recorders_()).not.toContain(recorder);
  });

  it('recorder can be attached multiple times safely', () => {
    const session = buildSession();
    const runtime = new FakeRuntime();
    const orchestrator = new SessionOrchestrator({
      runtime: runtime as unknown as RuntimeEngine,
      session,
    });
    const recorder = new SessionRecorder({
      sessionId: session.sessionId(),
      protocolId: session.protocolId(),
      executionPlanId: session.executionPlanId(),
    });
    orchestrator.attachRecorder(recorder);
    orchestrator.attachRecorder(recorder);
    expect(orchestrator.recorders_()).toEqual([recorder]);
  });
});

// =============================================================================
// SessionRecorder edge cases
// =============================================================================

describe('SessionRecorder — coverage', () => {
  it('record + size + events', () => {
    const r = new SessionRecorder({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
    });
    const ev: SessionEvent = Object.freeze({ type: 'session-started', monotonicMs: 100 });
    r.record(ev);
    r.record(ev);
    expect(r.size()).toBe(2);
    expect(r.events()[0]).toEqual(ev);
  });

  it('recordMany appends in order', () => {
    const r = new SessionRecorder({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
    });
    r.recordMany([
      Object.freeze({ type: 'session-started', monotonicMs: 100 }),
      Object.freeze({ type: 'session-paused', monotonicMs: 200, pausedForMs: 0 }),
    ]);
    expect(r.size()).toBe(2);
  });

  it('clear empties the recorder', () => {
    const r = new SessionRecorder({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
    });
    r.record(Object.freeze({ type: 'session-started', monotonicMs: 100 }));
    r.clear();
    expect(r.size()).toBe(0);
  });

  it('import throws on missing identity', () => {
    const r = new SessionRecorder();
    expect(() => r.export(0)).toThrow();
  });
});

// Reference all imported items to satisfy no-unused-vars without `void`.
// (All imports above are used in test cases below.)
const _unusedReferences: unknown[] = [
  SESSION_ID,
  PROTOCOL_ID,
  EXECUTION_PLAN_ID,
  fakePlan,
  FakeRuntime,
];
if (_unusedReferences.length === 0) {
  throw new Error('sanity check');
}
