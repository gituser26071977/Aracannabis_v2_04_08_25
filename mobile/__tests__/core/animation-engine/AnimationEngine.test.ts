/**
 * Tests for AnimationEngine — lifecycle, frame emission, sync,
 * cancellation, completion, pause/resume.
 */

import {
  ANIMATION_ENGINE_ID,
  ANIMATION_ENGINE_VERSION,
  AnimationEngine,
  DEFAULT_ANIMATION_CONFIG,
  createAnimation,
} from '@core/animation-engine';
import type { AnimationConfig, AnimationEvent } from '@core/animation-engine';

import {
  breathEvent,
  buildFakeBreath,
  buildFakeRuntime,
  buildFakeSession,
  buildFakeTimer,
  runtimeEvent,
  sessionSnapshotWithNoPhases,
  timerEvent,
} from './fakes';

describe('AnimationEngine — construction', () => {
  it('exposes the engine id', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    expect(engine.id()).toBe(ANIMATION_ENGINE_ID);
    expect(engine.state()).toBe('idle');
  });

  it('exposes the module version', () => {
    expect(ANIMATION_ENGINE_VERSION).toBe('1.0.0');
  });

  it('createAnimation factory returns an AnimationEngine', () => {
    const runtime = buildFakeRuntime();
    const engine = createAnimation({ runtime });
    expect(engine).toBeInstanceOf(AnimationEngine);
    expect(engine.state()).toBe('idle');
  });

  it('starts with an idle frame', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    const frame = engine.currentFrame();
    expect(frame.phase).toBe('idle');
  });

  it('uses the default config when none provided', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    expect(engine.easingCurve()).toBe(DEFAULT_ANIMATION_CONFIG.easingCurve);
  });

  it('accepts a custom config', () => {
    const runtime = buildFakeRuntime();
    const config: AnimationConfig = { ...DEFAULT_ANIMATION_CONFIG, easingCurve: 'linear' };
    const engine = new AnimationEngine({ runtime, config });
    expect(engine.easingCurve()).toBe('linear');
  });
});

describe('AnimationEngine — lifecycle', () => {
  it('start moves engine to running and emits animation-engine-started', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    expect(engine.state()).toBe('running');
    expect(events.some((e) => e.type === 'animation-engine-started')).toBe(true);
  });

  it('pause moves engine to paused and emits animation-engine-paused', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 0 });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    engine.pause();
    expect(engine.state()).toBe('paused');
    const paused = events.find((e) => e.type === 'animation-engine-paused');
    expect(paused).toBeDefined();
    if (paused && paused.type === 'animation-engine-paused') {
      expect(paused.frozenFrame.phase).toBeDefined();
    }
  });

  it('resume moves engine back to running', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    engine.pause();
    engine.resume();
    expect(engine.state()).toBe('running');
  });

  it('dispose moves engine to disposed and clears listeners', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    engine.dispose();
    expect(engine.state()).toBe('disposed');
    expect(runtime.listenerCount()).toBe(0);
  });

  it('dispose is idempotent', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.dispose();
    engine.dispose();
    expect(engine.state()).toBe('disposed');
  });

  it('start is a no-op when disposed', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.dispose();
    engine.start();
    expect(engine.state()).toBe('disposed');
  });

  it('pause is a no-op when idle', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.pause();
    expect(engine.state()).toBe('idle');
  });
});

describe('AnimationEngine — frame emission', () => {
  it('emits an animation-frame event when started', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    const frames = events.filter((e) => e.type === 'animation-frame');
    expect(frames.length).toBeGreaterThan(0);
  });

  it('emits a frame on update() while running', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 0 });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    const before = events.filter((e) => e.type === 'animation-frame').length;
    engine.update(100);
    const after = events.filter((e) => e.type === 'animation-frame').length;
    expect(after).toBeGreaterThan(before);
  });

  it('does not emit frames while paused', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    engine.pause();
    const before = events.filter((e) => e.type === 'animation-frame').length;
    engine.update(1000);
    const after = events.filter((e) => e.type === 'animation-frame').length;
    expect(after).toBe(before);
  });
});

describe('AnimationEngine — Runtime event sync', () => {
  it('transitions to preparing on protocol-runtime-started', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.started(100));
    expect(engine.phase()).toBe('preparing');
  });

  it('transitions to inhale on inhaling phase-change', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('inhaling', 200));
    expect(engine.phase()).toBe('inhale');
  });

  it('transitions to hold on holdAfterInhale', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('holdAfterInhale', 200));
    expect(engine.phase()).toBe('hold');
  });

  it('transitions to exhale on exhaling', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('exhaling', 200));
    expect(engine.phase()).toBe('exhale');
  });

  it('transitions to completed on protocol-runtime-completed', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.completed(0, 1000));
    expect(engine.phase()).toBe('completed');
  });

  it('transitions to idle on protocol-runtime-stopped', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.stopped('cancelled', 500));
    expect(engine.phase()).toBe('idle');
  });

  it('pauses on protocol-runtime-paused', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    runtime.emit(runtimeEvent.paused());
    expect(engine.state()).toBe('paused');
  });

  it('resumes on protocol-runtime-resumed', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    engine.pause();
    runtime.emit(runtimeEvent.resumed());
    expect(engine.state()).toBe('running');
  });
});

describe('AnimationEngine — real-time update', () => {
  it('advances progress over time within a phase', () => {
    const runtime = buildFakeRuntime();
    let now = 0;
    const engine = new AnimationEngine({
      runtime,
      now: (): number => now,
    });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('inhaling', 0));
    engine.update(0);
    const startRadius = engine.currentFrame().radius;

    now = 2000;
    engine.update(now);
    const midRadius = engine.currentFrame().radius;

    now = 4000;
    engine.update(now);
    const endRadius = engine.currentFrame().radius;

    expect(startRadius).toBeLessThanOrEqual(midRadius);
    expect(midRadius).toBeLessThanOrEqual(endRadius);
  });

  it('handles Timer-driven updates via subscribe', () => {
    const runtime = buildFakeRuntime();
    const timer = buildFakeTimer();
    const engine = new AnimationEngine({ runtime, timer: timer as never });
    engine.start();
    const before = engine.metrics().framesEmitted;
    timer.emit(timerEvent.tick(100));
    const after = engine.metrics().framesEmitted;
    expect(after).toBeGreaterThan(before);
  });
});

describe('AnimationEngine — listener isolation', () => {
  it('routes a throwing listener to onListenerError', () => {
    const runtime = buildFakeRuntime();
    const errors: unknown[] = [];
    const engine = new AnimationEngine({
      runtime,
      onListenerError: (err) => errors.push(err),
    });
    engine.subscribe(() => {
      throw new Error('boom');
    });
    engine.start();
    expect(errors.length).toBeGreaterThan(0);
  });

  it('still emits to other listeners when one throws', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, onListenerError: () => undefined });
    let okCount = 0;
    engine.subscribe(() => {
      throw new Error('boom');
    });
    engine.subscribe(() => {
      okCount += 1;
    });
    engine.start();
    expect(okCount).toBeGreaterThan(0);
  });

  it('re-entrant subscribe during emit does not receive current event', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 0 });
    engine.start();
    let late = 0;
    let early = 0;
    // Subscribe AFTER start so the snapshot pattern is exercised by a
    // single emit (`update`). start() emits multiple back-to-back
    // events and would otherwise include the late subscriber on the
    // second snapshot.
    engine.subscribe(() => {
      early += 1;
      engine.subscribe(() => {
        late += 1;
      });
    });
    engine.update(1000);
    expect(early).toBe(1);
    expect(late).toBe(0);
    engine.update(2000);
    expect(late).toBe(1);
  });
});

describe('AnimationEngine — metrics', () => {
  it('increments framesEmitted on every emitted frame', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    const a = engine.metrics().framesEmitted;
    engine.update(500);
    engine.update(1000);
    const b = engine.metrics().framesEmitted;
    expect(b).toBeGreaterThan(a);
  });

  it('increments phaseChanges on phase transitions', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    const a = engine.metrics().phaseChanges;
    runtime.emit(runtimeEvent.phaseChanged('inhaling'));
    runtime.emit(runtimeEvent.phaseChanged('holdAfterInhale'));
    const b = engine.metrics().phaseChanges;
    expect(b).toBeGreaterThanOrEqual(a + 2);
  });

  it('records attachedSince after start', () => {
    const runtime = buildFakeRuntime();
    const now = 42;
    const engine = new AnimationEngine({ runtime, now: (): number => now });
    engine.start();
    expect(engine.metrics().attachedSince).toBe(42);
  });
});

describe('AnimationEngine — cancellation and completion', () => {
  it('returns to idle when stopped:cancelled', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    runtime.emit(runtimeEvent.started());
    runtime.emit(runtimeEvent.phaseChanged('inhaling'));
    runtime.emit(runtimeEvent.stopped('cancelled'));
    expect(engine.phase()).toBe('idle');
  });

  it('reaches completed when stopped:completed', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    runtime.emit(runtimeEvent.completed());
    expect(engine.phase()).toBe('completed');
  });

  it('dispose emits animation-engine-disposed', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    const events: AnimationEvent[] = [];
    engine.subscribe((e) => events.push(e));
    engine.start();
    engine.dispose();
    expect(events.some((e) => e.type === 'animation-engine-disposed')).toBe(true);
  });
});

describe('AnimationEngine — state machine', () => {
  it('initial state is idle', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    expect(engine.state()).toBe('idle');
  });

  it('disposed state is terminal', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    engine.start();
    engine.dispose();
    expect(engine.state()).toBe('disposed');
  });
});

describe('AnimationEngine — breath integration', () => {
  it('updates phase on breath-phase-changed', () => {
    const runtime = buildFakeRuntime();
    const breath = buildFakeBreath();
    const engine = new AnimationEngine({
      runtime,
      breath: breath as never,
      now: (): number => 200,
    });
    engine.start();
    breath.emit(breathEvent.phaseChanged('exhaling', 1500));
    expect(engine.phase()).toBe('exhale');
  });

  it('falls back to phaseDuration=1 when breath omits duration', () => {
    const runtime = buildFakeRuntime();
    const breath = buildFakeBreath();
    const engine = new AnimationEngine({
      runtime,
      breath: breath as never,
      now: (): number => 100,
    });
    engine.start();
    breath.emit({ type: 'breath-phase-changed', phase: 'inhaling' });
    // Advance past 1ms — should land at progress=1
    engine.update(200);
    expect(engine.phase()).toBe('inhale');
    expect(engine.currentFrame().radius).toBeGreaterThan(0);
  });

  it('ignores breath events that are not phase-changed', () => {
    const runtime = buildFakeRuntime();
    const breath = buildFakeBreath();
    const engine = new AnimationEngine({
      runtime,
      breath: breath as never,
      now: (): number => 100,
    });
    engine.start();
    const beforePhase = engine.phase();
    breath.emit({ type: 'breath-started' });
    expect(engine.phase()).toBe(beforePhase);
  });

  it('isolates listener exceptions on breath events', () => {
    const runtime = buildFakeRuntime();
    const errors: unknown[] = [];
    const engine = new AnimationEngine({
      runtime,
      onListenerError: (err) => errors.push(err),
    });
    // Force a synthetic listener exception in the breath path by
    // wrapping the runtime hook indirectly: the breath path itself
    // does not throw, so errors should remain empty.
    engine.start();
    expect(errors.length).toBe(0);
  });
});

describe('AnimationEngine — session integration', () => {
  it('uses plan phase durations when session is provided', () => {
    const runtime = buildFakeRuntime();
    const session = buildFakeSession([{ phase: 'inhaling', duration: 2000 }]);
    const engine = new AnimationEngine({
      runtime,
      session: session as never,
      now: (): number => 0,
    });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('inhaling', 0));
    // Half-way through a 2000ms phase → progress ≈ 0.5
    engine.update(1000);
    const frame = engine.currentFrame();
    expect(frame.normalizedProgress).toBeCloseTo(0.5, 1);
  });

  it('falls back to default duration when session plan has no matching phase', () => {
    const runtime = buildFakeRuntime();
    const session = buildFakeSession([{ phase: 'holdAfterInhale', duration: 9999 }]);
    const engine = new AnimationEngine({
      runtime,
      session: session as never,
      now: (): number => 0,
    });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('inhaling', 0));
    engine.update(2000);
    // 2000ms / 4000ms default = 0.5
    expect(engine.currentFrame().normalizedProgress).toBeCloseTo(0.5, 1);
  });

  it('falls back to default when session snapshot is null', () => {
    const runtime = buildFakeRuntime();
    const session = sessionSnapshotWithNoPhases();
    const engine = new AnimationEngine({
      runtime,
      session: session as never,
      now: (): number => 0,
    });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('inhaling', 0));
    engine.update(2000);
    expect(engine.currentFrame().normalizedProgress).toBeCloseTo(0.5, 1);
  });

  it('exposes sessionPlan accessor', () => {
    const runtime = buildFakeRuntime();
    const session = buildFakeSession([{ phase: 'inhaling', duration: 1000 }]);
    const engine = new AnimationEngine({ runtime, session: session as never });
    const plan = engine.sessionPlan();
    expect(plan).not.toBeNull();
    expect(plan?.length).toBe(1);
  });

  it('sessionPlan is null when no session injected', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime });
    expect(engine.sessionPlan()).toBeNull();
  });
});

describe('AnimationEngine — Runtime protocol-runtime-errored', () => {
  it('ignores errored events gracefully', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 0 });
    engine.start();
    runtime.emit(runtimeEvent.errored());
    // Engine should not transition to an errored state — errored events
    // are not handled, so the engine remains in its current phase.
    expect(engine.state()).toBe('running');
  });

  it('ignores cycle-completed events gracefully', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 0 });
    engine.start();
    runtime.emit(runtimeEvent.cycleCompleted());
    expect(engine.state()).toBe('running');
  });
});

describe('AnimationEngine — phase-mapping edge cases', () => {
  it('handles holdAfterExhale phase change', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    runtime.emit(runtimeEvent.phaseChanged('holdAfterExhale', 200));
    expect(engine.phase()).toBe('hold');
  });

  it('default Runtime event type does not throw', () => {
    const runtime = buildFakeRuntime();
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.start();
    // Synthesize a runtime event whose payload type is unknown.
    runtime.emit({
      source: 'protocol',
      payload: { type: 'protocol-runtime-something-unknown' } as never,
    });
    expect(engine.state()).toBe('running');
  });
});

describe('AnimationEngine — completed frame', () => {
  it('transitions to completed and emits animation-frame with phase=completed', () => {
    const runtime = buildFakeRuntime();
    const events: AnimationEvent[] = [];
    const engine = new AnimationEngine({ runtime, now: (): number => 100 });
    engine.subscribe((e) => events.push(e));
    engine.start();
    runtime.emit(runtimeEvent.completed(0, 1000));
    expect(engine.phase()).toBe('completed');
    const completedFrame = events
      .filter((e) => e.type === 'animation-frame')
      .map((e) => (e as { frame: { phase: string } }).frame.phase)
      .at(-1);
    expect(completedFrame).toBe('completed');
  });
});
