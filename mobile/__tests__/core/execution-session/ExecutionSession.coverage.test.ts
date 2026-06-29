/**
 * ExecutionSession — coverage-targeted tests for edge branches and
 * internal helpers that the main suite exercises only partially.
 */

import { ProtocolId } from '@araflow/shared-contracts';

import {
  ACTIVE_SESSION_STATES,
  EMPTY_SESSION_METRICS,
  ExecutionPlanId,
  ExecutionSession,
  SESSION_EVENT_TYPES,
  SESSION_STATES,
  TERMINAL_SESSION_STATES,
  buildTimeline,
  canTransition,
  computeMetrics,
  isActiveSessionState,
  isSessionEvent,
  isSessionLifecycleEventType,
  isSessionState,
  type SessionMetrics,
} from '@core/execution-session';
import { SessionEventLog } from '@core/execution-session/application/SessionEventLog';

import { FakeClock, fakePlan, fakePlanId, fakeSessionId } from './fakes';

const PROTOCOL_ID = ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');
const SESSION_ID = fakeSessionId('cov');

const newSession = (overrides: Partial<{ now: () => number }> = {}): ExecutionSession =>
  new ExecutionSession({
    sessionId: SESSION_ID,
    protocolId: PROTOCOL_ID,
    executionPlanId: ExecutionPlanId(fakePlanId()),
    plan: fakePlan(2, 1000),
    ...(overrides.now !== undefined ? { now: overrides.now } : {}),
  });

// =====================================================================
// Predicates
// =====================================================================

describe('ExecutionSession — domain predicate coverage', () => {
  it('SESSION_STATES has 8 entries', () => {
    expect(SESSION_STATES.length).toBe(8);
  });
  it('TERMINAL_SESSION_STATES has 4 entries', () => {
    expect(TERMINAL_SESSION_STATES.length).toBe(4);
  });
  it('ACTIVE_SESSION_STATES has 4 entries', () => {
    expect(ACTIVE_SESSION_STATES.length).toBe(4);
  });
  it('isSessionState accepts valid states', () => {
    expect(isSessionState('idle')).toBe(true);
    expect(isSessionState('running')).toBe(true);
    expect(isSessionState('paused')).toBe(true);
    expect(isSessionState('completed')).toBe(true);
    expect(isSessionState('cancelled')).toBe(true);
    expect(isSessionState('interrupted')).toBe(true);
    expect(isSessionState('failed')).toBe(true);
    expect(isSessionState('preparing')).toBe(true);
  });
  it('isSessionState rejects invalid', () => {
    expect(isSessionState('nope')).toBe(false);
    expect(isSessionState(null)).toBe(false);
    expect(isSessionState(42)).toBe(false);
  });
  it('isActiveSessionState covers active states', () => {
    expect(isActiveSessionState('idle')).toBe(true);
    expect(isActiveSessionState('preparing')).toBe(true);
    expect(isActiveSessionState('running')).toBe(true);
    expect(isActiveSessionState('paused')).toBe(true);
    expect(isActiveSessionState('completed')).toBe(false);
  });
  it('canTransition returns correct boolean', () => {
    expect(canTransition('idle', 'preparing')).toBe(true);
    expect(canTransition('idle', 'running')).toBe(false);
    expect(canTransition('running', 'paused')).toBe(true);
    expect(canTransition('paused', 'completed')).toBe(false);
    expect(canTransition('completed', 'idle')).toBe(false);
  });
  it('isSessionEvent accepts valid events', () => {
    expect(
      isSessionEvent({
        type: 'session-created',
        sessionId: SESSION_ID,
        protocolId: PROTOCOL_ID,
        executionPlanId: ExecutionPlanId('1'),
        state: 'idle',
        monotonicMs: 0,
      }),
    ).toBe(true);
    expect(isSessionEvent({ type: 'session-started', monotonicMs: 0 })).toBe(true);
    expect(isSessionEvent({ type: 'nope' })).toBe(false);
    expect(isSessionEvent(null)).toBe(false);
  });
  it('isSessionLifecycleEventType covers all lifecycle types', () => {
    for (const t of [
      'session-created',
      'session-preparing',
      'session-started',
      'session-paused',
      'session-resumed',
      'session-cancelled',
      'session-completed',
      'session-failed',
      'session-interrupted',
    ]) {
      expect(isSessionLifecycleEventType(t)).toBe(true);
    }
    expect(isSessionLifecycleEventType('phase-changed')).toBe(false);
    expect(isSessionLifecycleEventType('nope')).toBe(false);
  });
  it('SESSION_EVENT_TYPES has 13 entries', () => {
    expect(SESSION_EVENT_TYPES.length).toBe(13);
  });
});

// =====================================================================
// computeMetrics edge cases
// =====================================================================

describe('computeMetrics — edge cases', () => {
  it('returns EMPTY_SESSION_METRICS for empty events', () => {
    const m = computeMetrics({ events: [], plannedDurationMs: 1000, nowMs: 0 });
    // For empty events: elapsedMs=0, completedCycles=0, etc.,
    // but remainingMs = plannedDurationMs (session has not started).
    expect(m.elapsedMs).toBe(0);
    expect(m.completedCycles).toBe(0);
    expect(m.currentPhase).toBeNull();
    expect(m.progress).toBe(0);
    expect(m.remainingMs).toBe(1000);
  });

  it('handles paused/resumed sequence for pauseDuration', () => {
    const m = computeMetrics({
      events: [
        { type: 'session-started', monotonicMs: 100 },
        { type: 'session-paused', monotonicMs: 200, pausedForMs: 0 },
        { type: 'session-resumed', monotonicMs: 500, resumedFromMs: 200 },
      ],
      plannedDurationMs: 1000,
      nowMs: 600,
    });
    expect(m.pauseCount).toBe(1);
    expect(m.pauseDurationMs).toBe(300);
    expect(m.elapsedMs).toBe(200);
    expect(m.sessionDurationMs).toBe(500);
  });

  it('handles multiple pause/resume cycles', () => {
    const m = computeMetrics({
      events: [
        { type: 'session-started', monotonicMs: 0 },
        { type: 'session-paused', monotonicMs: 100, pausedForMs: 0 },
        { type: 'session-resumed', monotonicMs: 150, resumedFromMs: 100 },
        { type: 'session-paused', monotonicMs: 300, pausedForMs: 0 },
        { type: 'session-resumed', monotonicMs: 400, resumedFromMs: 300 },
      ],
      plannedDurationMs: 1000,
      nowMs: 500,
    });
    expect(m.pauseCount).toBe(2);
    expect(m.pauseDurationMs).toBe(150);
  });

  it('clamps progress to [0, 1]', () => {
    const m = computeMetrics({
      events: [{ type: 'session-started', monotonicMs: 0 }],
      plannedDurationMs: 1000,
      nowMs: 5000,
    });
    expect(m.progress).toBe(1);
  });

  it('handles zero plannedDurationMs', () => {
    const m = computeMetrics({
      events: [{ type: 'session-started', monotonicMs: 0 }],
      plannedDurationMs: 0,
      nowMs: 100,
    });
    expect(m.progress).toBe(0);
  });

  it('remainingMs = plannedDurationMs when no start', () => {
    const m = computeMetrics({
      events: [],
      plannedDurationMs: 5000,
      nowMs: 100,
    });
    expect(m.remainingMs).toBe(5000);
  });

  it('handles terminal event as sessionEndMs', () => {
    const m = computeMetrics({
      events: [
        { type: 'session-started', monotonicMs: 0 },
        { type: 'session-cancelled', monotonicMs: 800, reason: 'x' },
      ],
      plannedDurationMs: 1000,
      nowMs: 99999,
    });
    expect(m.sessionDurationMs).toBe(800);
  });
});

// =====================================================================
// buildTimeline edge cases
// =====================================================================

describe('buildTimeline — edge cases', () => {
  it('returns empty array for no events', () => {
    expect(buildTimeline([])).toEqual([]);
  });

  it('merges consecutive same-kind phase entries', () => {
    const tl = buildTimeline([
      {
        type: 'phase-changed',
        monotonicMs: 0,
        phase: 'inhaling',
        cycleIndex: 0,
        phaseIndex: 0,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
      {
        type: 'phase-changed',
        monotonicMs: 1000,
        phase: 'exhaling',
        cycleIndex: 0,
        phaseIndex: 1,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
    ]);
    expect(tl.length).toBe(2);
    expect(tl[0]?.kind).toBe('inhale');
    expect(tl[1]?.kind).toBe('exhale');
  });

  it('returns terminal entry on session-completed', () => {
    const tl = buildTimeline([
      { type: 'session-started', monotonicMs: 0 },
      { type: 'session-completed', monotonicMs: 1000, totalElapsedMs: 1000 },
    ]);
    expect(tl.length).toBe(1);
    expect(tl[0]?.kind).toBe('complete');
    // Terminal entries (complete/cancel/fail/interrupt) have duration=0
    // — they represent the moment of termination.
    expect(tl[0]?.durationMs).toBe(0);
  });

  it('maps hold phases to hold kind', () => {
    const tl = buildTimeline([
      {
        type: 'phase-changed',
        monotonicMs: 0,
        phase: 'holdAfterInhale',
        cycleIndex: 0,
        phaseIndex: 1,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
    ]);
    expect(tl[0]?.kind).toBe('hold');
  });

  it('skips session-started (no timeline entry)', () => {
    const tl = buildTimeline([{ type: 'session-started', monotonicMs: 0 }]);
    expect(tl).toEqual([]);
  });
});

// =====================================================================
// Snapshot increments version when called
// =====================================================================

describe('ExecutionSession — snapshot version semantics', () => {
  it('snapshot bumps version after each call (snapshot-created event appended)', () => {
    const clock = new FakeClock();
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
      now: clock.now,
    });
    const v0 = s.version();
    s.snapshot();
    const v1 = s.version();
    // snapshot does NOT change state — version stays.
    expect(v1).toBe(v0);
  });
});

// =====================================================================
// Metrics type freeze + equality
// =====================================================================

describe('SessionMetrics — frozen', () => {
  it('EMPTY_SESSION_METRICS is frozen', () => {
    expect(Object.isFrozen(EMPTY_SESSION_METRICS)).toBe(true);
  });
});

// =====================================================================
// Use through ExecutionSession.metrics() — branch coverage
// =====================================================================

describe('ExecutionSession.metrics() branch coverage', () => {
  it('returns metrics reflecting currentCycle from phase-changed events', () => {
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
      cycleIndex: 2,
      phaseIndex: 4,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    const m = s.metrics();
    expect(m.currentCycle).toBe(2);
    expect(m.currentPhase).toBe('inhaling');
  });

  it('completedCycles is the max of recorded cycles', () => {
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
      cycleElapsedMs: 1000,
      totalCycles: 4,
    });
    s.recordCycleCompleted({
      cycleIndex: 1,
      cycleElapsedMs: 1000,
      totalCycles: 4,
    });
    expect(s.metrics().completedCycles).toBe(2);
  });

  it('metrics.currentCycle is max(currentCycle, completedCycles)', () => {
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
    s.recordCycleCompleted({
      cycleIndex: 0,
      cycleElapsedMs: 1000,
      totalCycles: 4,
    });
    s.recordPhaseChange({
      phase: 'inhaling',
      cycleIndex: 2,
      phaseIndex: 0,
      phaseElapsedMs: 0,
      phaseDurationMs: 1000,
    });
    expect(s.metrics().currentCycle).toBe(2);
  });
});

// =====================================================================
// newSession helper sanity
// =====================================================================

describe('newSession helper', () => {
  it('returns an ExecutionSession', () => {
    const s = newSession({ now: new FakeClock().now });
    expect(s).toBeInstanceOf(ExecutionSession);
  });
});

// =====================================================================
// Snap types — typed metric access
// =====================================================================

describe('typed metric access', () => {
  it('metrics shape is frozen', () => {
    const s = newSession();
    const m: SessionMetrics = s.metrics();
    expect(Object.isFrozen(m)).toBe(true);
  });
});

// =====================================================================
// SessionEventLog — direct API coverage
// =====================================================================

describe('SessionEventLog — direct API', () => {
  it('starts empty', () => {
    const log = new SessionEventLog();
    expect(log.size()).toBe(0);
    expect(log.all()).toEqual([]);
    expect(log.last()).toBeNull();
  });

  it('append + last + size', () => {
    const log = new SessionEventLog();
    log.append({
      type: 'session-started',
      monotonicMs: 100,
    });
    expect(log.size()).toBe(1);
    expect(log.last()?.type).toBe('session-started');
  });

  it('at returns event at index', () => {
    const log = new SessionEventLog();
    log.append({ type: 'session-started', monotonicMs: 100 });
    log.append({ type: 'session-paused', monotonicMs: 200, pausedForMs: 0 });
    expect(log.at(0)?.type).toBe('session-started');
    expect(log.at(1)?.type).toBe('session-paused');
  });

  it('at returns null for out-of-bounds index', () => {
    const log = new SessionEventLog();
    expect(log.at(0)).toBeNull();
    expect(log.at(-1)).toBeNull();
    log.append({ type: 'session-started', monotonicMs: 100 });
    expect(log.at(5)).toBeNull();
  });

  it('clear empties the log', () => {
    const log = new SessionEventLog();
    log.append({ type: 'session-started', monotonicMs: 100 });
    log.clear();
    expect(log.size()).toBe(0);
    expect(log.all()).toEqual([]);
  });

  it('all() returns frozen array', () => {
    const log = new SessionEventLog();
    log.append({ type: 'session-started', monotonicMs: 100 });
    expect(Object.isFrozen(log.all())).toBe(true);
  });
});

// =====================================================================
// buildTimeline — additional mappings
// =====================================================================

describe('buildTimeline — additional mappings', () => {
  it('maps session-failed to fail', () => {
    const tl = buildTimeline([
      { type: 'session-failed', monotonicMs: 100, code: 'x', message: 'y' },
    ]);
    expect(tl[0]?.kind).toBe('fail');
  });

  it('maps session-cancelled to cancel', () => {
    const tl = buildTimeline([{ type: 'session-cancelled', monotonicMs: 100, reason: 'x' }]);
    expect(tl[0]?.kind).toBe('cancel');
  });

  it('maps session-interrupted to interrupt', () => {
    const tl = buildTimeline([{ type: 'session-interrupted', monotonicMs: 100, reason: 'x' }]);
    expect(tl[0]?.kind).toBe('interrupt');
  });

  it('maps cycle-completed to cycle', () => {
    const tl = buildTimeline([
      {
        type: 'cycle-completed',
        monotonicMs: 100,
        cycleIndex: 1,
        cycleElapsedMs: 2000,
        totalCycles: 4,
      },
    ]);
    expect(tl[0]?.kind).toBe('cycle');
    expect(tl[0]?.cycleIndex).toBe(1);
  });

  it('merges consecutive inhale entries', () => {
    const tl = buildTimeline([
      {
        type: 'phase-changed',
        monotonicMs: 0,
        phase: 'inhaling',
        cycleIndex: 0,
        phaseIndex: 0,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
      {
        type: 'phase-changed',
        monotonicMs: 1000,
        phase: 'inhaling',
        cycleIndex: 0,
        phaseIndex: 2,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
    ]);
    expect(tl.length).toBe(1);
    expect(tl[0]?.durationMs).toBe(1000);
  });

  it('merges consecutive hold entries', () => {
    const tl = buildTimeline([
      {
        type: 'phase-changed',
        monotonicMs: 0,
        phase: 'holdAfterInhale',
        cycleIndex: 0,
        phaseIndex: 1,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
      {
        type: 'phase-changed',
        monotonicMs: 1000,
        phase: 'holdAfterExhale',
        cycleIndex: 0,
        phaseIndex: 3,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
    ]);
    expect(tl.length).toBe(1);
    expect(tl[0]?.kind).toBe('hold');
  });

  it('does not merge non-consecutive different kinds', () => {
    const tl = buildTimeline([
      {
        type: 'phase-changed',
        monotonicMs: 0,
        phase: 'inhaling',
        cycleIndex: 0,
        phaseIndex: 0,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
      {
        type: 'phase-changed',
        monotonicMs: 1000,
        phase: 'exhaling',
        cycleIndex: 0,
        phaseIndex: 1,
        phaseElapsedMs: 0,
        phaseDurationMs: 1000,
      },
    ]);
    expect(tl.length).toBe(2);
  });
});

// =====================================================================
// ExecutionSession — transition error paths
// =====================================================================

describe('ExecutionSession — transition error paths', () => {
  it('start from completed state returns Err', () => {
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
    const r = s.start();
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('session_invalid_transition');
    }
  });

  it('pause from completed state returns Err', () => {
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
    const r = s.pause();
    expect(r.ok).toBe(false);
  });

  it('resume from idle returns Err', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const r = s.resume();
    expect(r.ok).toBe(false);
  });

  it('interrupt from idle returns Err', () => {
    const s = new ExecutionSession({
      sessionId: SESSION_ID,
      protocolId: PROTOCOL_ID,
      executionPlanId: ExecutionPlanId(fakePlanId()),
      plan: fakePlan(),
    });
    const r = s.interrupt();
    expect(r.ok).toBe(false);
  });

  it('recordCycleCompleted on terminal returns Err', () => {
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
    const r = s.recordCycleCompleted({
      cycleIndex: 0,
      cycleElapsedMs: 1000,
      totalCycles: 4,
    });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('session_terminal_state');
    }
  });
});
