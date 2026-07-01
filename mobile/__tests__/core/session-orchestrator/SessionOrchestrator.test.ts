/**
 * Tests for SessionOrchestrator.
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
  SessionOrchestrator,
  type SessionOrchestratorDeps,
  SessionRecorder,
} from '@core/session-orchestrator';

import { fakePlan } from './fake-plan';
import { FakeRuntime, runtimeEvent, anchorSessionCreated } from './fakes';

// =============================================================================
// Helpers
// =============================================================================

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

interface BuildArgs {
  readonly runtime?: FakeRuntime;
  readonly session?: ExecutionSession;
  readonly recorder?: SessionRecorder;
  readonly onListenerError?: (e: unknown) => void;
}

const buildOrchestrator = (
  args: BuildArgs = {},
): {
  orchestrator: SessionOrchestrator;
  runtime: FakeRuntime;
  session: ExecutionSession;
  recorder: SessionRecorder;
} => {
  const runtime = args.runtime ?? new FakeRuntime();
  const session = args.session ?? buildSession();
  const recorder =
    args.recorder ??
    new SessionRecorder({
      sessionId: session.sessionId(),
      protocolId: session.protocolId(),
      executionPlanId: session.executionPlanId(),
    });
  const deps: SessionOrchestratorDeps = {
    runtime: runtime as unknown as RuntimeEngine,
    session,
    ...(args.onListenerError === undefined ? {} : { onListenerError: args.onListenerError }),
  };
  const orchestrator = new SessionOrchestrator(deps);
  if (args.recorder === undefined) {
    orchestrator.attachRecorder(recorder);
  }
  return { orchestrator, runtime, session, recorder };
};

// =============================================================================
// Construction & identity
// =============================================================================

describe('SessionOrchestrator — construction', () => {
  it('starts in detached state', () => {
    const { orchestrator } = buildOrchestrator();
    expect(orchestrator.state()).toBe('detached');
    expect(orchestrator.isDisposed()).toBe(false);
  });

  it('exposes identity from Session', () => {
    const { orchestrator } = buildOrchestrator();
    expect(orchestrator.sessionId()).toBe(SESSION_ID);
    expect(orchestrator.protocolId()).toBe(PROTOCOL_ID);
  });

  it('exposes Runtime and Session states', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    expect(orchestrator.runtimeState()).toBe('uninitialized');
    expect(orchestrator.sessionState()).toBe('idle');
    runtime.setState('running');
    session.start();
    expect(orchestrator.runtimeState()).toBe('running');
    expect(orchestrator.sessionState()).toBe('running');
  });

  it('starts with empty inconsistency reports', () => {
    const { orchestrator } = buildOrchestrator();
    expect(orchestrator.inconsistencies()).toEqual([]);
  });

  it('starts with zero metrics', () => {
    const { orchestrator } = buildOrchestrator();
    const m = orchestrator.metrics();
    expect(m.eventsProcessed).toBe(0);
    expect(m.eventsSkipped).toBe(0);
    expect(m.inconsistencies).toBe(0);
    expect(m.replays).toBe(0);
  });
});

// =============================================================================
// attach / detach / FSM
// =============================================================================

describe('SessionOrchestrator — attach / detach', () => {
  it('attach transitions detached → attached', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    const r = orchestrator.attach();
    expect(r.ok).toBe(true);
    expect(orchestrator.state()).toBe('attached');
    expect(runtime.listenerCount()).toBe(1);
  });

  it('attach is idempotent', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    orchestrator.attach();
    expect(runtime.listenerCount()).toBe(1);
  });

  it('detach transitions attached → detached and unsubscribes', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    orchestrator.detach();
    expect(orchestrator.state()).toBe('detached');
    expect(runtime.listenerCount()).toBe(0);
  });

  it('detach when detached is no-op', () => {
    const { orchestrator } = buildOrchestrator();
    const r = orchestrator.detach();
    expect(r.ok).toBe(true);
    expect(orchestrator.state()).toBe('detached');
  });

  it('emits orchestrator-attached and orchestrator-detached', () => {
    const { orchestrator } = buildOrchestrator();
    const events: string[] = [];
    orchestrator.subscribe((e) => {
      events.push(e.type);
    });
    orchestrator.attach();
    orchestrator.detach();
    expect(events).toEqual(['orchestrator-attached', 'orchestrator-detached']);
  });

  it('attach after dispose returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    const r = orchestrator.attach();
    expect(r.ok).toBe(false);
  });

  it('detach after dispose returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    const r = orchestrator.detach();
    expect(r.ok).toBe(false);
  });
});

// =============================================================================
// Forwarding Runtime events → Session API
// =============================================================================

describe('SessionOrchestrator — event forwarding', () => {
  it('protocol-runtime-started → session.start()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    expect(session.state()).toBe('running');
  });

  it('protocol-runtime-paused → session.pause()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.paused());
    expect(session.state()).toBe('paused');
  });

  it('protocol-runtime-resumed → session.resume()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.paused());
    runtime.emit(runtimeEvent.resumed());
    expect(session.state()).toBe('running');
  });

  it('protocol-runtime-completed → session.complete()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    expect(session.state()).toBe('completed');
  });

  it('protocol-runtime-stopped:cancelled → session.cancel()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.stoppedCancelled());
    expect(session.state()).toBe('cancelled');
  });

  it('protocol-runtime-stopped:errored → session.fail()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.stoppedErrored());
    expect(session.state()).toBe('failed');
  });

  it('protocol-runtime-errored → session.fail()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.errored(200, 'e_code', 'boom'));
    expect(session.state()).toBe('failed');
  });

  it('runtime-error → session.fail()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.runtimeError(60, 'rt_code', 'rt boom'));
    expect(session.state()).toBe('failed');
  });

  it('runtime-compile-failed is skipped (session stays idle)', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.runtimeCompileFailed(50));
    expect(session.state()).toBe('idle');
  });

  it('runtime-compile-failed while session past idle produces divergence', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.runtimeCompileFailed(50));
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'divergence')).toBe(true);
  });

  it('runtime-disposed → session.dispose()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.runtimeDisposed());
    expect(session.isDisposed()).toBe(true);
  });

  it('protocol-runtime-phase-changed → session.recordPhaseChange()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.phaseChanged(130, 'inhaling', 0));
    const metrics = session.metrics();
    expect(metrics.currentPhase).toBe('inhaling');
    expect(metrics.currentCycle).toBe(0);
  });

  it('protocol-runtime-cycle-completed → session.recordCycleCompleted()', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.cycleCompleted(140, 0));
    const metrics = session.metrics();
    expect(metrics.completedCycles).toBe(1);
  });

  it('timer and breath events are skipped (not translated)', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.timerTick());
    runtime.emit(runtimeEvent.breathPhaseChanged());
    const m = orchestrator.metrics();
    expect(m.eventsSkipped).toBe(2);
    expect(m.eventsProcessed).toBe(0);
  });

  it('does not forward events when detached', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    runtime.emit(runtimeEvent.started());
    expect(session.state()).toBe('idle');
    const m = orchestrator.metrics();
    expect(m.eventsProcessed).toBe(0);
  });

  it('does not forward events after dispose', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    orchestrator.dispose();
    runtime.emit(runtimeEvent.started());
    expect(session.state()).toBe('idle');
  });

  it('runtime-completed → session.complete() (idempotent)', () => {
    const { orchestrator, runtime, session } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    runtime.emit(runtimeEvent.runtimeCompleted(260));
    expect(session.state()).toBe('completed');
  });

  it('runtime-warnings is skipped', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.runtimeWarnings());
    const m = orchestrator.metrics();
    expect(m.eventsSkipped).toBe(1);
  });
});

// =============================================================================
// Inconsistency detection
// =============================================================================

describe('SessionOrchestrator — inconsistency detection', () => {
  it('out-of-order event produces report', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.phaseChanged(200));
    runtime.emit(runtimeEvent.phaseChanged(100));
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'out-of-order')).toBe(true);
  });

  it('pause while idle is impossible-state', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.paused());
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('resume while not paused is impossible-state', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.resumed());
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('completed while idle is impossible-state', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.completed());
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('started while not idle is impossible-state', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.started());
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'impossible-state')).toBe(true);
  });

  it('invalid cycle index produces invalid-cycle report', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.cycleCompleted(140, 999));
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'invalid-cycle')).toBe(true);
  });

  it('invalid phase produces invalid-phase report', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.phaseChanged(130, 'holdAfterExhale' as never, 0));
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'invalid-phase')).toBe(true);
  });

  it('runtime-error while session is terminal produces divergence', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    runtime.emit(runtimeEvent.runtimeError(300));
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'divergence')).toBe(true);
  });

  it('inconsistency metric counts reports', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.paused());
    runtime.emit(runtimeEvent.resumed());
    const m = orchestrator.metrics();
    expect(m.inconsistencies).toBeGreaterThan(0);
  });

  it('emits orchestrator-inconsistency events', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    const events: string[] = [];
    orchestrator.subscribe((e) => {
      events.push(e.type);
    });
    orchestrator.attach();
    runtime.emit(runtimeEvent.paused());
    expect(events).toContain('orchestrator-inconsistency');
  });

  it('previousPhase invalid produces invalid-phase', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    // Manually craft a phase-changed with invalid previousPhase
    runtime.emit({
      source: 'protocol',
      payload: {
        type: 'protocol-runtime-phase-changed',
        executionId: '01HXYZ00000000000000000000' as never,
        previousPhase: 'fictionalPhase' as never,
        currentPhase: 'inhaling',
        cycleIndex: 0,
        phaseProgress: 0,
        monotonicMs: 200,
      },
    });
    const reports = orchestrator.inconsistencies();
    expect(reports.some((r) => r.kind === 'invalid-phase')).toBe(true);
  });
});

// =============================================================================
// Recorder integration
// =============================================================================

describe('SessionOrchestrator — recorder integration', () => {
  it('attached recorder receives session events', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    expect(recorder.size()).toBeGreaterThan(0);
    const events = recorder.events();
    expect(events.some((e: SessionEvent) => e.type === 'session-started')).toBe(true);
  });

  it('recorder can be detached', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.detachRecorder(recorder);
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    expect(recorder.size()).toBe(0);
  });

  it('attachRecorder is idempotent', () => {
    const { orchestrator, recorder } = buildOrchestrator();
    const r1 = orchestrator.attachRecorder(recorder);
    const r2 = orchestrator.attachRecorder(recorder);
    expect(r1.ok && r2.ok).toBe(true);
    expect(orchestrator.recorders_()).toEqual([recorder]);
  });

  it('export produces a SessionRecording', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    const recording = recorder.export(1000);
    expect(recording.version).toBe(1);
    expect(recording.eventCount).toBeGreaterThan(0);
    expect(recording.events.length).toBeGreaterThan(0);
    expect(recording.recordedAtMonotonicMs).toBe(1000);
  });

  it('export without identity throws', () => {
    const r = new SessionRecorder();
    expect(() => r.export(0)).toThrow();
  });

  it('import round-trips a recording', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    const recording = recorder.export(1000);
    const imported = SessionRecorder.import(recording);
    expect(imported.size()).toBe(recording.events.length);
    expect(imported.sessionId()).toBe(recording.sessionId);
  });

  it('exportJson + importJson round-trip', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    const json = recorder.exportJson(1000);
    const imported = SessionRecorder.importJson(json);
    expect(imported.size()).toBe(json.events.length);
  });

  it('recorder events include session-created anchor', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    const events = recorder.events();
    expect(events[0]?.type).toBe('session-created');
  });

  it('multiple recorders all receive events', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    const r1 = new SessionRecorder({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
    });
    const r2 = new SessionRecorder({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: EXECUTION_PLAN_ID,
    });
    orchestrator.attachRecorder(r1);
    orchestrator.attachRecorder(r2);
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    expect(r1.size()).toBeGreaterThan(0);
    expect(r2.size()).toBeGreaterThan(0);
  });
});

// =============================================================================
// Replay
// =============================================================================

describe('SessionOrchestrator — replay', () => {
  it('replays events into the existing session', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    const recording = recorder.export(1000);

    const session2 = buildSession();
    const rt2 = new FakeRuntime();
    const orch2 = new SessionOrchestrator({
      runtime: rt2 as unknown as RuntimeEngine,
      session: session2,
    });
    const r = orch2.replay(recording.events);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.value.state()).toBe('completed');
    }
    expect(orch2.metrics().replays).toBe(1);
  });

  it('replay with plan reconstructs a fresh session', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    const recording = recorder.export(1000);
    const r = orchestrator.replay(recording.events, fakePlan());
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.value.state()).toBe('completed');
      expect(r.value.sessionId()).toBe(orchestrator.sessionId());
    }
  });

  it('replay with empty events returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    const r = orchestrator.replay([]);
    expect(r.ok).toBe(false);
  });

  it('replay with non-anchor first event returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    const ev: SessionEvent = Object.freeze({
      type: 'session-started',
      monotonicMs: 100,
    });
    const r = orchestrator.replay([ev]);
    expect(r.ok).toBe(false);
  });

  it('replay emits orchestrator-replayed event', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    const recording = recorder.export(1000);
    const events: string[] = [];
    orchestrator.subscribe((e) => {
      events.push(e.type);
    });
    orchestrator.replay(recording.events, fakePlan());
    expect(events).toContain('orchestrator-replayed');
  });

  it('replay of identity-mismatched events returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    const wrongAnchor = anchorSessionCreated('01ARZ3NDEKTSV4RRFFQ69G5F99' as SessionId);
    const r = orchestrator.replay([wrongAnchor]);
    expect(r.ok).toBe(false);
  });

  it('SessionOrchestrator.replayIntoSession static works', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    const recording = recorder.export(1000);
    const r = SessionOrchestrator.replayIntoSession({
      recording,
      plan: fakePlan(),
    });
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.value.state()).toBe('completed');
    }
  });

  it('replay is deterministic', () => {
    const { orchestrator, runtime, recorder } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.paused());
    runtime.emit(runtimeEvent.resumed());
    runtime.emit(runtimeEvent.completed());
    const recording = recorder.export(1000);

    const r1 = SessionOrchestrator.replayIntoSession({ recording, plan: fakePlan() });
    const r2 = SessionOrchestrator.replayIntoSession({ recording, plan: fakePlan() });
    expect(r1.ok && r2.ok).toBe(true);
    if (r1.ok && r2.ok) {
      const ev1 = r1.value.events();
      const ev2 = r2.value.events();
      expect(ev1.length).toBe(ev2.length);
      expect(ev1.map((e: SessionEvent) => e.type)).toEqual(ev2.map((e: SessionEvent) => e.type));
    }
  });

  it('replay after dispose returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    const r = orchestrator.replay([anchorSessionCreated()]);
    expect(r.ok).toBe(false);
  });
});

// =============================================================================
// Concurrency / multiple listeners
// =============================================================================

describe('SessionOrchestrator — concurrency', () => {
  it('listener that subscribes during emit does not block others', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    const order: string[] = [];
    orchestrator.subscribe(() => {
      order.push('a');
    });
    orchestrator.subscribe(() => {
      order.push('b');
    });
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.completed());
    expect(order.length).toBeGreaterThan(0);
  });

  it('throwing listener does not break others', () => {
    const { orchestrator } = buildOrchestrator();
    const captured: string[] = [];
    orchestrator.subscribe(() => {
      throw new Error('boom');
    });
    orchestrator.subscribe(() => {
      captured.push('ok');
    });
    orchestrator.attach();
    orchestrator.sessionSnapshot(); // emit orchestrator event
    expect(captured).toContain('ok');
  });

  it('listener error routes to onListenerError', () => {
    const errors: unknown[] = [];
    const orchestrator = new SessionOrchestrator({
      runtime: new FakeRuntime() as unknown as RuntimeEngine,
      session: buildSession(),
      onListenerError: (e) => {
        errors.push(e);
      },
    });
    orchestrator.subscribe(() => {
      throw new Error('listener boom');
    });
    orchestrator.attach();
    expect(errors.length).toBeGreaterThanOrEqual(1);
  });
});

// =============================================================================
// Dispose
// =============================================================================

describe('SessionOrchestrator — dispose', () => {
  it('transitions to disposed and emits event', () => {
    const { orchestrator } = buildOrchestrator();
    const events: string[] = [];
    orchestrator.subscribe((e) => {
      events.push(e.type);
    });
    orchestrator.attach();
    orchestrator.dispose();
    expect(orchestrator.state()).toBe('disposed');
    expect(orchestrator.isDisposed()).toBe(true);
    expect(events).toContain('orchestrator-disposed');
  });

  it('dispose unsubscribes from Runtime', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    orchestrator.dispose();
    expect(runtime.listenerCount()).toBe(0);
  });

  it('dispose is idempotent', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    const r = orchestrator.dispose();
    expect(r.ok).toBe(true);
  });

  it('dispose clears recorders and stream listeners', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    expect(orchestrator.recorders_()).toEqual([]);
  });

  it('attachRecorder after dispose returns Err', () => {
    const { orchestrator } = buildOrchestrator();
    orchestrator.dispose();
    const r = orchestrator.attachRecorder(new SessionRecorder());
    expect(r.ok).toBe(false);
  });
});

// =============================================================================
// Read models
// =============================================================================

describe('SessionOrchestrator — read models', () => {
  it('sessionSnapshot returns Session snapshot', () => {
    const { orchestrator } = buildOrchestrator();
    const snap = orchestrator.sessionSnapshot();
    expect(snap.state as SessionState).toBe('idle');
    expect(snap.sessionId).toBe(orchestrator.sessionId());
  });

  it('metrics include processed / skipped / replays / inconsistencies', () => {
    const { orchestrator, runtime } = buildOrchestrator();
    orchestrator.attach();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.timerTick());
    const m = orchestrator.metrics();
    expect(m.eventsProcessed).toBeGreaterThan(0);
    expect(m.eventsSkipped).toBeGreaterThan(0);
  });

  it('subscribe returns unsubscribe', () => {
    const { orchestrator } = buildOrchestrator();
    const unsub = orchestrator.subscribe(() => undefined);
    expect(typeof unsub).toBe('function');
    unsub();
  });
});
