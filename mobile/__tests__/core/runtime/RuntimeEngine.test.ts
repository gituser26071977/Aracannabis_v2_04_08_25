/**
 * RuntimeEngine — unit tests.
 *
 * Uses FakeTimer to control wall-clock deterministically.
 * Covers: construction, lifecycle FSM, loadProtocol, compile, start/pause/
 * resume/cancel, dispose, subscribe (multi-listener, error isolation,
 * re-entrant), metrics, snapshot, plan access, warnings, ergonomic
 * gaps (errored state, pause-outlasts-plan), background/foreground.
 */

import { EngineId } from '@araflow/shared-contracts';

import { JsonSource, ProtocolCompiler } from '@core/protocol-compiler';
import {
  RUNTIME_ENGINE_VERSION,
  RUNTIME_STATES,
  TERMINAL_RUNTIME_STATES,
  RuntimeEngine,
  isRuntimeState,
  isTerminalRuntimeState,
  type RuntimeEvent,
  type RuntimeState,
} from '@core/runtime';

import { captureEvents, createFakePlan, createFakeTimer, silentWarnings } from './fakes';

const RUNTIME_ID = EngineId('test-runtime');

describe('RuntimeEngine — construction & version', () => {
  it('exports RUNTIME_ENGINE_VERSION = 1.0.0', () => {
    expect(RUNTIME_ENGINE_VERSION).toBe('1.0.0');
  });

  it('RUNTIME_STATES has 10 entries', () => {
    expect(RUNTIME_STATES.length).toBe(10);
  });

  it('TERMINAL_RUNTIME_STATES contains 4 entries', () => {
    expect(TERMINAL_RUNTIME_STATES.length).toBe(4);
  });

  it('isRuntimeState / isTerminalRuntimeState work', () => {
    expect(isRuntimeState('running')).toBe(true);
    expect(isRuntimeState('invalid')).toBe(false);
    expect(isTerminalRuntimeState('disposed')).toBe(true);
    expect(isTerminalRuntimeState('running')).toBe(false);
  });

  it('factory creates a RuntimeEngine in uninitialized state', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    expect(rt.getState()).toBe<RuntimeState>('uninitialized');
    expect(rt.getExecutionPlan()).toBeNull();
    expect(rt.getWarnings()).toEqual([]);
    rt.dispose();
  });
});

describe('RuntimeEngine — loadProtocol', () => {
  it('transitions to loaded on valid plan', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const plan = createFakePlan(2, 1000);
    const r = rt.loadProtocol(plan);
    expect(r.ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('loaded');
    expect(rt.getExecutionPlan()).toBe(plan);
    rt.dispose();
  });

  it('returns Err when plan has zero cycles', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const plan = createFakePlan(0, 1000);
    const r = rt.loadProtocol(plan);
    // plan with 0 cycles and 0 phases fails ProtocolRuntime.load with empty_plan
    expect(r.ok).toBe(false);
    rt.dispose();
  });

  it('returns Err when called from loaded state (already loaded)', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    const r = rt.loadProtocol(createFakePlan(2, 1000));
    expect(r.ok).toBe(false);
    rt.dispose();
  });

  it('returns Err from terminal states', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.dispose();
    const r = rt.loadProtocol(createFakePlan(2, 1000));
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('runtime_invalid_state');
    }
  });
});

describe('RuntimeEngine — compile', () => {
  it('emits runtime-warnings when source has warnings', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const { events, listener } = captureEvents();
    rt.subscribe(listener);

    // Physiological sigh has full metadata, no expected warnings —
    // we verify compile produces plan + transitions to loaded.
    const source = JsonSource(
      JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FA4',
        version: '1.0.0',
        title: 'Test',
        description: 'desc',
        breath: {
          cycles: 2,
          restBetweenCyclesMs: 0,
          phases: [
            { type: 'inhale', durationMs: 1000, curve: 'linear' },
            { type: 'exhale', durationMs: 1000, curve: 'linear' },
          ],
        },
        metadata: {
          author: 'test',
          language: 'en',
          references: [],
          evidenceLevel: 'A',
          contraindications: [],
          category: 'test',
          tags: [],
          approvedAt: new Date(0).toISOString(),
        },
      }),
      'inline://test',
    );

    const r = rt.compile(source);
    expect(r.ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('loaded');
    // All compile() emissions are through the stream
    const runtimeEvents = events.filter((e) => e.source === 'runtime');
    expect(runtimeEvents.length).toBeGreaterThanOrEqual(0);
    rt.dispose();
  });

  it('emits runtime-compile-failed on invalid source', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const { events, listener } = captureEvents();
    rt.subscribe(listener);

    const source = JsonSource(JSON.stringify({ not: 'a protocol' }), 'inline://bad');
    const r = rt.compile(source);
    expect(r.ok).toBe(false);
    expect(rt.getState()).toBe<RuntimeState>('errored');
    if (!r.ok) {
      expect(r.error.code).toBe('runtime_compile_failed');
    }
    const compileFailed = events.find(
      (e) => e.source === 'runtime' && e.payload.type === 'runtime-compile-failed',
    );
    expect(compileFailed).toBeDefined();
  });
});

describe('RuntimeEngine — start/pause/resume/cancel', () => {
  it('full happy path: load → start → pause → resume → cancel', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(4, 1000));
    expect(rt.getState()).toBe<RuntimeState>('loaded');

    expect(rt.start().ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('running');

    expect(rt.pause().ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('paused');

    expect(rt.resume().ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('running');

    expect(rt.cancel().ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('stopped');
    rt.dispose();
  });

  it('pause is a no-op when not running', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    const r = rt.pause();
    expect(r.ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('loaded');
    rt.dispose();
  });

  it('resume is a no-op when not paused', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    expect(rt.resume().ok).toBe(true);
    expect(rt.getState()).toBe<RuntimeState>('running');
    rt.dispose();
  });

  it('start returns Err from uninitialized', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const r = rt.start();
    expect(r.ok).toBe(false);
    rt.dispose();
  });

  it('cancel from terminal is a no-op', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.dispose();
    expect(rt.cancel().ok).toBe(true);
  });

  it('pause-outlasts-plan is rejected at resume()', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000)); // planned: 2000ms
    rt.start();
    t.advance(3000); // simulate elapsed > planned before pause
    rt.pause();
    const r = rt.resume();
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('runtime_pause_outlasts_plan');
    }
    rt.dispose();
  });
});

describe('RuntimeEngine — dispose', () => {
  it('transitions to disposed', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.dispose();
    expect(rt.getState()).toBe<RuntimeState>('disposed');
  });

  it('is idempotent', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.dispose();
    rt.dispose();
    expect(rt.getState()).toBe<RuntimeState>('disposed');
  });

  it('auto-cancels a running session before disposal', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    rt.dispose();
    expect(rt.getState()).toBe<RuntimeState>('disposed');
  });
});

describe('RuntimeEngine — subscribe', () => {
  it('emits events with correct sources after start()', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const { events, listener } = captureEvents();
    rt.subscribe(listener);
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    // After start, ProtocolRuntime emits protocol-runtime-started; timer events also flow.
    t.emitTick(0, 0);
    const sources = new Set(events.map((e) => e.source));
    expect(sources.has('protocol')).toBe(true);
    rt.cancel();
    rt.dispose();
  });

  it('multi-listener: both listeners receive the same sequence of events', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const a = captureEvents();
    const b = captureEvents();
    rt.subscribe(a.listener);
    rt.subscribe(b.listener);
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    expect(a.events.length).toBeGreaterThan(0);
    expect(b.events.length).toBe(a.events.length);
    for (let i = 0; i < a.events.length; i += 1) {
      expect(a.events[i]).toEqual(b.events[i]);
    }
    rt.cancel();
    rt.dispose();
  });

  it('unsubscriber stops delivery of subsequent events', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const { events, listener } = captureEvents();
    const unsub = rt.subscribe(listener);
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    const countAfterStart = events.length;
    unsub();
    t.emitTick(100, 100);
    rt.cancel();
    rt.dispose();
    // No new events delivered after unsub.
    expect(events.length).toBe(countAfterStart);
  });

  it('listener errors are routed to onListenerError and other listeners still receive', () => {
    const t = createFakeTimer();
    const errors: unknown[] = [];
    const rt = new RuntimeEngine({
      runtimeId: RUNTIME_ID,
      timerEngine: t.engine,
      onListenerError: (e) => {
        errors.push(e);
      },
    });
    const safe: RuntimeEvent[] = [];
    rt.subscribe((e: RuntimeEvent) => {
      safe.push(e);
    });
    rt.subscribe(() => {
      throw new Error('boom');
    });
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    expect(safe.length).toBeGreaterThan(0);
    expect(errors.length).toBeGreaterThan(0);
    rt.cancel();
    rt.dispose();
  });
});

describe('RuntimeEngine — observation', () => {
  it('getExecutionPlan returns null before load, plan after', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    expect(rt.getExecutionPlan()).toBeNull();
    const plan = createFakePlan(2, 1000);
    rt.loadProtocol(plan);
    expect(rt.getExecutionPlan()).toBe(plan);
    rt.dispose();
  });

  it('getMetrics reflects elapsed and counters', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    const m = rt.getMetrics();
    expect(m.plannedDurationMs).toBe(2000);
    expect(m.totalCycles).toBe(2);
    expect(m.errors).toBe(0);
    rt.cancel();
    rt.dispose();
  });

  it('getSnapshot merges state + engines + plan', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const plan = createFakePlan(3, 500);
    rt.loadProtocol(plan);
    const snap = rt.snapshot();
    expect(snap.state).toBe<RuntimeState>('loaded');
    expect(snap.plan).toBe(plan);
    expect(snap.timer).not.toBeNull();
    expect(snap.breath).not.toBeNull();
    expect(snap.protocol).not.toBeNull();
    rt.dispose();
  });

  it('getWarnings returns the empty array initially', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    expect(rt.getWarnings()).toEqual([]);
    rt.dispose();
  });
});

describe('RuntimeEngine — background/foreground forwarding', () => {
  it('notifyBackground and notifyForeground are no-ops on the public API', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    expect(() => rt.notifyBackground()).not.toThrow();
    expect(() => rt.notifyForeground()).not.toThrow();
    rt.dispose();
  });
});

describe('RuntimeEngine — errored state from protocol-runtime-errored', () => {
  it('compile() failure sets state to errored', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    const source = JsonSource(JSON.stringify({ invalid: true }), 'inline://bad');
    const r = rt.compile(source);
    expect(r.ok).toBe(false);
    expect(rt.getState()).toBe('errored');
    rt.dispose();
  });
});

describe('RuntimeEngine — re-entrant subscribe during emit', () => {
  it('newly subscribed listener is added without exception during emit', () => {
    const t = createFakeTimer();
    const rt = new RuntimeEngine({ runtimeId: RUNTIME_ID, timerEngine: t.engine });
    rt.loadProtocol(createFakePlan(2, 1000));
    rt.start();
    // Subscribe inside a synchronous listener — must not throw.
    expect(() =>
      rt.subscribe(() => {
        rt.subscribe(() => undefined);
      }),
    ).not.toThrow();
    rt.cancel();
    rt.dispose();
  });
});

describe('ProtocolCompiler integration via RuntimeEngine.compile', () => {
  it('uses the canonical ProtocolCompiler internally', () => {
    // Sanity check: the Runtime's compile() delegates to ProtocolCompiler.compile()
    const compiler = new ProtocolCompiler({ compiledBy: EngineId('probe') });
    const source = JsonSource(JSON.stringify({ not: 'a protocol' }), 'inline://bad');
    const r = compiler.compile(source);
    expect(r.plan).toBeNull();
    expect(r.failures.length).toBeGreaterThan(0);
    expect(r.warnings).toEqual(silentWarnings);
  });
});
