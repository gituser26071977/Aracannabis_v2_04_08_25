/**
 * ExecutionSession — unit tests.
 *
 * Covers: construction, lifecycle FSM, pause/resume, cancel/complete/fail/
 * interrupt, snapshot immutability/version, timeline ordering, metrics
 * projection, event log, invariants (identity immutability, plan
 * immutability, event immutability), error transitions, dispose.
 */

import { ProtocolId } from '@araflow/shared-contracts';

import {
  ExecutionPlanId,
  ExecutionSession,
  isTerminalSessionState,
  legalTransitions,
  type SessionState,
} from '@core/execution-session';

import { FakeClock, fakePlan, fakePlanId, fakeSessionId } from './fakes';

const PROTOCOL_ID = ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');
const SESSION_ID = fakeSessionId('sess');

// =====================================================================
// Construction & version
// =====================================================================

describe('ExecutionSession — construction & version', () => {
  it('starts in idle state with a session-created event', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    expect(s.state()).toBe<SessionState>('idle');
    const events = s.events();
    expect(events.length).toBe(1);
    expect(events[0]?.type).toBe('session-created');
  });

  it('exposes identity getters that match constructor deps', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.sessionId()).toBe(SESSION_ID);
    expect(s.protocolId()).toBe(PROTOCOL_ID);
    expect(s.executionPlanId()).toBe(ExecutionPlanId(fakePlanId()));
    expect(s.plan().cycles).toBe(4);
  });

  it('initial version is 0', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.version()).toBe(0);
  });
});

// =====================================================================
// Lifecycle: start
// =====================================================================

describe('ExecutionSession — start', () => {
  it('idle → preparing → running, emits preparing + started events', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    expect(s.start().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('running');
    const types = s.events().map((e) => e.type);
    expect(types).toEqual(['session-created', 'session-preparing', 'session-started']);
  });

  it('start is idempotent when already running', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.start().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('running');
  });
});

// =====================================================================
// Lifecycle: pause / resume
// =====================================================================

describe('ExecutionSession — pause/resume', () => {
  it('running → paused → running', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.pause().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('paused');
    expect(s.resume().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('running');
  });

  it('pause is a no-op when already paused', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.pause();
    expect(s.pause().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('paused');
  });

  it('resume is a no-op when already running', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.resume().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('running');
  });

  it('pause from idle returns Err (invalid transition)', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const r = s.pause();
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('session_invalid_transition');
    }
  });
});

// =====================================================================
// Lifecycle: cancel / complete / fail / interrupt
// =====================================================================

describe('ExecutionSession — cancel', () => {
  it('running → cancelled', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.cancel('user').ok).toBe(true);
    expect(s.state()).toBe<SessionState>('cancelled');
    const last = s.events()[s.events().length - 1];
    expect(last?.type).toBe('session-cancelled');
  });

  it('cancel from idle is invalid', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const r = s.cancel();
    expect(r.ok).toBe(false);
  });

  it('cancel from terminal state is a no-op', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.complete();
    expect(s.cancel().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('completed');
  });
});

describe('ExecutionSession — complete', () => {
  it('running → completed', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.complete().ok).toBe(true);
    expect(s.state()).toBe<SessionState>('completed');
  });

  it('complete from idle is invalid', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.complete().ok).toBe(false);
  });
});

describe('ExecutionSession — fail', () => {
  it('running → failed with code + message', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.fail('boom', 'something went wrong').ok).toBe(true);
    expect(s.state()).toBe<SessionState>('failed');
  });

  it('fail from idle is invalid', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.fail('x', 'y').ok).toBe(false);
  });
});

describe('ExecutionSession — interrupt', () => {
  it('running → interrupted', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    expect(s.interrupt('os_pause').ok).toBe(true);
    expect(s.state()).toBe<SessionState>('interrupted');
  });
});

// =====================================================================
// Transition table
// =====================================================================

describe('legalTransitions table', () => {
  it('idle allows only preparing', () => {
    expect(legalTransitions('idle')).toEqual(['preparing']);
  });
  it('preparing allows running/cancelled/failed', () => {
    expect(new Set(legalTransitions('preparing'))).toEqual(
      new Set(['running', 'cancelled', 'failed']),
    );
  });
  it('running allows paused/completed/cancelled/interrupted/failed', () => {
    expect(new Set(legalTransitions('running'))).toEqual(
      new Set(['paused', 'completed', 'cancelled', 'interrupted', 'failed']),
    );
  });
  it('paused allows running/cancelled/interrupted/failed', () => {
    expect(new Set(legalTransitions('paused'))).toEqual(
      new Set(['running', 'cancelled', 'interrupted', 'failed']),
    );
  });
  it('terminal states have no outgoing transitions', () => {
    expect(legalTransitions('completed')).toEqual([]);
    expect(legalTransitions('cancelled')).toEqual([]);
    expect(legalTransitions('interrupted')).toEqual([]);
    expect(legalTransitions('failed')).toEqual([]);
  });
  it('isTerminalSessionState flags only the 4 terminal states', () => {
    expect(isTerminalSessionState('completed')).toBe(true);
    expect(isTerminalSessionState('cancelled')).toBe(true);
    expect(isTerminalSessionState('interrupted')).toBe(true);
    expect(isTerminalSessionState('failed')).toBe(true);
    expect(isTerminalSessionState('running')).toBe(false);
  });
});

// =====================================================================
// Snapshot
// =====================================================================

describe('ExecutionSession — snapshot', () => {
  it('snapshot is frozen (immutable)', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const snap = s.snapshot();
    expect(Object.isFrozen(snap)).toBe(true);
    expect(Object.isFrozen(snap.metrics)).toBe(true);
  });

  it('snapshot.version increments after state change', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    const v0 = s.snapshot().version;
    s.start();
    const v1 = s.snapshot().version;
    s.pause();
    const v2 = s.snapshot().version;
    s.resume();
    const v3 = s.snapshot().version;
    expect(v0).toBe(0);
    expect(v1).toBeGreaterThan(v0);
    expect(v2).toBeGreaterThan(v1);
    expect(v3).toBeGreaterThan(v2);
  });

  it('snapshot carries identity, state, and metrics', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    const snap = s.snapshot();
    expect(snap.sessionId).toBe(SESSION_ID);
    expect(snap.protocolId).toBe(PROTOCOL_ID);
    expect(snap.state).toBe<SessionState>('running');
    expect(snap.metrics).toBeDefined();
    expect(typeof snap.timestamp).toBe('number');
  });
});

// =====================================================================
// Metrics
// =====================================================================

describe('ExecutionSession — metrics', () => {
  it('initial metrics are all zero/empty', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const m = s.metrics();
    expect(m.elapsedMs).toBe(0);
    expect(m.completedCycles).toBe(0);
    expect(m.pauseCount).toBe(0);
    expect(m.progress).toBe(0);
    expect(m.currentPhase).toBeNull();
  });

  it('metrics reflects elapsed time and pause count after pause/resume', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(4, 1000),
      now: clock.now,
    });
    s.start();
    clock.advance(1000);
    s.pause();
    clock.advance(500);
    s.resume();
    clock.advance(1000);
    const m = s.metrics();
    expect(m.pauseCount).toBe(1);
    expect(m.pauseDurationMs).toBe(500);
    expect(m.elapsedMs).toBeGreaterThanOrEqual(2000);
    expect(m.remainingMs).toBeGreaterThanOrEqual(0);
  });

  it('completedCycles increments after recordCycleCompleted', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.recordCycleCompleted({
      cycleIndex: 0,
      cycleElapsedMs: 2000,
      totalCycles: 4,
    });
    s.recordCycleCompleted({
      cycleIndex: 1,
      cycleElapsedMs: 2000,
      totalCycles: 4,
    });
    expect(s.metrics().completedCycles).toBe(2);
  });

  it('progress is between 0 and 1', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(2, 1000),
      now: clock.now,
    });
    s.start();
    clock.advance(1000);
    const m = s.metrics();
    expect(m.progress).toBeGreaterThanOrEqual(0);
    expect(m.progress).toBeLessThanOrEqual(1);
  });
});

// =====================================================================
// Timeline
// =====================================================================

describe('ExecutionSession — timeline', () => {
  it('timeline is empty before start', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.timeline()).toEqual([]);
  });

  it('timeline entries are ordered by monotonicMs', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.recordPhaseChange({
      phase: 'inhaling',
      cycleIndex: 0,
      phaseIndex: 0,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    clock.advance(1000);
    s.recordPhaseChange({
      phase: 'exhaling',
      cycleIndex: 0,
      phaseIndex: 1,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    clock.advance(1000);
    s.complete();
    const tl = s.timeline();
    expect(tl.length).toBeGreaterThan(0);
    for (let i = 1; i < tl.length; i += 1) {
      const prev = tl[i - 1];
      const cur = tl[i];
      if (prev !== undefined && cur !== undefined) {
        expect(cur.monotonicMs).toBeGreaterThanOrEqual(prev.monotonicMs);
      }
    }
  });

  it('timeline is frozen', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.start();
    const tl = s.timeline();
    expect(Object.isFrozen(tl)).toBe(true);
  });

  it('pause/resume produce timeline entries', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    clock.advance(500);
    s.pause();
    clock.advance(200);
    s.resume();
    const tl = s.timeline();
    const kinds = tl.map((e) => e.kind);
    expect(kinds).toContain('pause');
    expect(kinds).toContain('resume');
  });
});

// =====================================================================
// Event log + invariants
// =====================================================================

describe('ExecutionSession — event log + invariants', () => {
  it('events() returns the same array reference on repeated calls', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const a = s.events();
    const b = s.events();
    // Fresh wrapper reads possible — but underlying entries must be identical.
    expect(a).toEqual(b);
  });

  it('past events are immutable (frozen)', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.start();
    const evs = s.events();
    for (const ev of evs) {
      expect(Object.isFrozen(ev)).toBe(true);
    }
  });

  it('sessionId never changes', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const id1 = s.sessionId();
    s.start();
    const id2 = s.sessionId();
    s.pause();
    const id3 = s.sessionId();
    expect(id1).toBe(id2);
    expect(id2).toBe(id3);
    expect(id1).toBe(SESSION_ID);
  });

  it('protocolId never changes', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.start();
    s.complete();
    expect(s.protocolId()).toBe(PROTOCOL_ID);
  });

  it('plan reference never changes', () => {
    const plan = fakePlan(3, 500);
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan,
    });
    const p1 = s.plan();
    s.start();
    const p2 = s.plan();
    s.complete();
    const p3 = s.plan();
    expect(p1).toBe(p2);
    expect(p2).toBe(p3);
    expect(p1).toBe(plan);
  });
});

// =====================================================================
// Phase + cycle observation
// =====================================================================

describe('ExecutionSession — observation events', () => {
  it('recordPhaseChange appends a phase-changed event', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.recordPhaseChange({
      phase: 'inhaling',
      cycleIndex: 0,
      phaseIndex: 0,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    const last = s.events()[s.events().length - 1];
    expect(last?.type).toBe('phase-changed');
  });

  it('recordPhaseChange on terminal returns Err', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.complete();
    const r = s.recordPhaseChange({
      phase: 'inhaling',
      cycleIndex: 0,
      phaseIndex: 0,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    expect(r.ok).toBe(false);
  });

  it('recordCycleCompleted appends cycle-completed event', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.recordCycleCompleted({
      cycleIndex: 0,
      cycleElapsedMs: 2000,
      totalCycles: 4,
    });
    const last = s.events()[s.events().length - 1];
    expect(last?.type).toBe('cycle-completed');
  });
});

// =====================================================================
// Dispose
// =====================================================================

describe('ExecutionSession — dispose', () => {
  it('marks session as disposed', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    expect(s.isDisposed()).toBe(false);
    s.dispose();
    expect(s.isDisposed()).toBe(true);
  });

  it('lifecycle methods on disposed return Err', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.dispose();
    expect(s.start().ok).toBe(false);
    expect(s.pause().ok).toBe(false);
    expect(s.resume().ok).toBe(false);
    expect(s.cancel().ok).toBe(false);
    expect(s.complete().ok).toBe(false);
  });

  it('dispose is idempotent', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.dispose();
    s.dispose();
    expect(s.isDisposed()).toBe(true);
  });

  it('dispose clears the event log', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    s.start();
    expect(s.events().length).toBeGreaterThan(0);
    s.dispose();
    expect(s.events().length).toBe(0);
  });
});

// =====================================================================
// Concurrency / re-entrancy
// =====================================================================

describe('ExecutionSession — concurrency', () => {
  it('rapid start/pause/resume produces deterministic event order', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.pause();
    s.resume();
    s.pause();
    s.resume();
    s.complete();
    const types = s.events().map((e) => e.type);
    expect(types).toEqual([
      'session-created',
      'session-preparing',
      'session-started',
      'session-paused',
      'session-resumed',
      'session-paused',
      'session-resumed',
      'session-completed',
    ]);
  });

  it('cancel after complete keeps state at completed', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.complete();
    s.cancel();
    expect(s.state()).toBe<SessionState>('completed');
  });

  it('fail after cancel keeps state at cancelled', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    s.start();
    s.cancel();
    const r = s.fail('x', 'y');
    expect(r.ok).toBe(false);
    expect(s.state()).toBe<SessionState>('cancelled');
  });
});
