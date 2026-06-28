/**
 * BreathEngine — main unit tests.
 *
 * Tests cover:
 *   - Construction & validation
 *   - Lifecycle (start, cancel, reset)
 *   - Phase transitions and events
 *   - Cycle transitions
 *   - Completion
 *   - Cancellation
 *   - Interruption (background/foreground)
 *   - Re-entrancy (subscribe/cancel inside listener)
 *   - Error handling
 *   - Snapshot correctness
 */

import { BreathEngine, computeCycleMs, type BreathCycleConfig } from '@core/breath-engine';

import { createBreathTestRig } from './fakes';

const BOX_CONFIG: BreathCycleConfig = {
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 3,
};

const PREP_CONFIG: BreathCycleConfig = {
  ...BOX_CONFIG,
  prepMs: 2_000,
};

const NO_HOLD_CONFIG: BreathCycleConfig = {
  inhaleMs: 5_000,
  holdAfterInhaleMs: 0,
  exhaleMs: 5_000,
  holdAfterExhaleMs: 0,
  cycles: 2,
};

describe('BreathEngine — construction', () => {
  test('rejects missing monotonic clock', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    expect(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      new BreathEngine({ monotonic: undefined as any, timerEngine: rig.timerEngine, config: BOX_CONFIG });
    }).toThrow(/monotonic/);
  });

  test('rejects missing timerEngine', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    expect(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      new BreathEngine({ monotonic: rig.monotonic, timerEngine: undefined as any, config: BOX_CONFIG });
    }).toThrow(/timerEngine/);
  });

  test('rejects invalid config (zero inhale)', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    expect(() => {
      new BreathEngine({
        monotonic: rig.monotonic,
        timerEngine: rig.timerEngine,
        config: { ...BOX_CONFIG, inhaleMs: 0 },
      });
    }).toThrow();
  });

  test('rejects invalid config (zero cycles)', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    expect(() => {
      new BreathEngine({
        monotonic: rig.monotonic,
        timerEngine: rig.timerEngine,
        config: { ...BOX_CONFIG, cycles: 0 },
      });
    }).toThrow();
  });

  test('starts in idle state', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    expect(rig.breathEngine.getState()).toBe('idle');
    expect(rig.breathEngine.getCurrentPhase()).toBeNull();
    expect(rig.breathEngine.snapshot().totalElapsedMs).toBe(0);
  });
});

describe('BreathEngine — start (no prep)', () => {
  test('transitions to inhaling and emits breath-started + cycle-started + phase-changed', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();

    expect(rig.breathEngine.getState()).toBe('inhaling');
    expect(rig.breathEvents.map((e) => e.type)).toEqual([
      'breath-started',
      'cycle-started',
      'phase-changed',
    ]);
  });

  test('breath-started event has correct payload', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    const ev = rig.breathEvents.find((e) => e.type === 'breath-started');
    expect(ev).toBeDefined();
    if (ev && ev.type === 'breath-started') {
      expect(ev.totalCycles).toBe(BOX_CONFIG.cycles);
      expect(ev.totalDurationMs).toBe(computeCycleMs(BOX_CONFIG) * BOX_CONFIG.cycles);
    }
  });

  test('phase-changed event has null previousPhase', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    const ev = rig.breathEvents.find((e) => e.type === 'phase-changed');
    if (ev && ev.type === 'phase-changed') {
      expect(ev.previousPhase).toBeNull();
      expect(ev.currentPhase).toBe('inhaling');
      expect(ev.cycleIndex).toBe(0);
      expect(ev.phaseProgress).toBe(0);
    }
  });

  test('throws when start called twice without reset', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    expect(() => rig.breathEngine.start()).toThrow();
  });
});

describe('BreathEngine — start (with prep)', () => {
  test('transitions to preparing and emits only breath-started', () => {
    const rig = createBreathTestRig(PREP_CONFIG);
    rig.breathEngine.start();

    expect(rig.breathEngine.getState()).toBe('preparing');
    expect(rig.breathEngine.getCurrentPhase()).toBeNull();
    expect(rig.breathEvents.map((e) => e.type)).toEqual(['breath-started']);
  });

  test('prep phase transitions to inhaling on tick', () => {
    const rig = createBreathTestRig(PREP_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(PREP_CONFIG.prepMs ?? 0 + 200); // cross prep boundary
    const phaseChange = rig.breathEvents.find((e) => e.type === 'phase-changed');
    expect(phaseChange).toBeDefined();
    expect(rig.breathEngine.getState()).toBe('inhaling');
  });
});

describe('BreathEngine — phase progression through a cycle', () => {
  test('progresses inhaling → holdAfterInhale → exhaling → holdAfterExhale', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();

    // Drive through one full cycle (16s).
    rig.clock.advance(16_000);

    const phaseEvents = rig.breathEvents.filter((e) => e.type === 'phase-changed');
    const phaseSequence = phaseEvents
      .map((e) => (e.type === 'phase-changed' ? e.currentPhase : null))
      .filter((p): p is NonNullable<typeof p> => p !== null);

    expect(phaseSequence).toContain('inhaling');
    expect(phaseSequence).toContain('holdAfterInhale');
    expect(phaseSequence).toContain('exhaling');
    expect(phaseSequence).toContain('holdAfterExhale');
  });

  test('emits breath-completed when exhale ends', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(12_000); // through inhale + holdAfterInhale + exhale
    const breathCompleted = rig.breathEvents.find((e) => e.type === 'breath-completed');
    expect(breathCompleted).toBeDefined();
    if (breathCompleted && breathCompleted.type === 'breath-completed') {
      expect(breathCompleted.cycleIndex).toBe(0);
    }
  });

  test('emits cycle-completed when holdAfterExhale ends', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(16_000);
    const cycleCompleted = rig.breathEvents.find((e) => e.type === 'cycle-completed');
    expect(cycleCompleted).toBeDefined();
    if (cycleCompleted && cycleCompleted.type === 'cycle-completed') {
      expect(cycleCompleted.cycleIndex).toBe(0);
    }
  });
});

describe('BreathEngine — multiple cycles', () => {
  test('emits 3 cycle-started and 3 cycle-completed for 3 cycles', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(48_000); // 3 full cycles

    const cycleStarted = rig.breathEvents.filter((e) => e.type === 'cycle-started');
    const cycleCompleted = rig.breathEvents.filter((e) => e.type === 'cycle-completed');
    expect(cycleStarted.length).toBe(3);
    expect(cycleCompleted.length).toBe(3);
  });

  test('emits completed event at session end', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(48_000);
    const completed = rig.breathEvents.find((e) => e.type === 'completed');
    expect(completed).toBeDefined();
    expect(rig.breathEngine.getState()).toBe('completed');
  });

  test('cyclesCompleted counter increments', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(32_000); // 2 cycles
    expect(rig.breathEngine.getCyclesCompleted()).toBe(2);
  });
});

describe('BreathEngine — cancellation', () => {
  test('cancels active session and emits cancelled event', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(2_000);
    rig.breathEngine.cancel();

    expect(rig.breathEngine.getState()).toBe('cancelled');
    const cancelled = rig.breathEvents.find((e) => e.type === 'cancelled');
    expect(cancelled).toBeDefined();
    if (cancelled && cancelled.type === 'cancelled') {
      expect(cancelled.stateBefore).toBe('inhaling');
      expect(cancelled.elapsedAtCancelMs).toBeGreaterThan(0);
    }
  });

  test('cancel is no-op when idle', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.cancel();
    expect(rig.breathEvents.filter((e) => e.type === 'cancelled')).toHaveLength(0);
  });

  test('cancel is no-op after completion', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(48_000);
    const beforeCount = rig.breathEvents.length;
    rig.breathEngine.cancel();
    expect(rig.breathEvents.length).toBe(beforeCount);
  });

  test('can restart after cancel', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.breathEngine.cancel();
    expect(() => rig.breathEngine.start()).not.toThrow();
    expect(rig.breathEngine.getState()).toBe('inhaling');
  });

  test('can restart after completion', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(48_000);
    expect(rig.breathEngine.getState()).toBe('completed');
    expect(() => rig.breathEngine.start()).not.toThrow();
  });
});

describe('BreathEngine — reset', () => {
  test('reset clears state', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(8_000);
    rig.breathEngine.reset();
    expect(rig.breathEngine.getState()).toBe('idle');
    expect(rig.breathEngine.getSessionElapsedMs()).toBe(0);
    expect(rig.breathEngine.snapshot().depth).toBe(0);
  });

  test('reset does not reset Timer Engine', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(8_000);
    rig.breathEngine.reset();
    expect(rig.timerEngine.getState()).toBe('running');
  });
});

describe('BreathEngine — interruption', () => {
  test('enters interrupted state on background', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(2_000);
    rig.timerEngine.notifyBackground();
    expect(rig.breathEngine.getState()).toBe('interrupted');
    const interrupted = rig.breathEvents.find((e) => e.type === 'interrupted');
    expect(interrupted).toBeDefined();
  });

  test('resumes from interrupted on foreground', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(2_000);
    rig.timerEngine.notifyBackground();
    rig.timerEngine.notifyForeground();

    expect(rig.breathEngine.getState()).toBe('inhaling');
    const resumed = rig.breathEvents.find((e) => e.type === 'resumed-from-interrupt');
    expect(resumed).toBeDefined();
  });

  test('cancel works from interrupted state', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(2_000);
    rig.timerEngine.notifyBackground();
    rig.breathEngine.cancel();
    expect(rig.breathEngine.getState()).toBe('cancelled');
  });
});

describe('BreathEngine — snapshot', () => {
  test('initial snapshot is empty', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    const snap = rig.breathEngine.snapshot();
    expect(snap.state).toBe('idle');
    expect(snap.phase).toBeNull();
    expect(snap.depth).toBe(0);
    expect(snap.totalCycles).toBe(BOX_CONFIG.cycles);
  });

  test('snapshot reflects current phase during session', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(6_000); // mid holdAfterInhale
    const snap = rig.breathEngine.snapshot();
    expect(snap.state).toBe('holdAfterInhale');
    expect(snap.cycleIndex).toBe(0);
    expect(snap.depth).toBe(1); // holdAfterInhale = full
  });

  test('depth follows curve during inhaling', () => {
    const rig = createBreathTestRig(BOX_CONFIG, { timerMode: 'high-precision' });
    rig.breathEngine.start();
    rig.clock.advance(2_000); // 50% through inhale (linear)
    const snap = rig.breathEngine.snapshot();
    expect(snap.phase).toBe('inhaling');
    expect(snap.phaseProgress).toBeCloseTo(0.5, 1);
    // default curve is easeInOut
    expect(snap.depth).toBeGreaterThan(0);
    expect(snap.depth).toBeLessThanOrEqual(1);
  });
});

describe('BreathEngine — re-entrancy', () => {
  test('subscribe during dispatch does not break iteration', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    const off1 = rig.breathEngine.subscribe((e) => {
      if (e.type === 'phase-changed') {
        // Subscribing during dispatch.
        rig.breathEngine.subscribe(() => undefined);
      }
    });
    rig.breathEngine.start();
    off1();
    // No error thrown
  });

  test('unsubscribe during dispatch does not affect current iteration', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    let off2: () => void = () => undefined;
    off2 = rig.breathEngine.subscribe((e) => {
      if (e.type === 'phase-changed') {
        off2(); // unsubscribe self during dispatch
      }
    });
    rig.breathEngine.start();
    off2();
  });

  test('listener errors are swallowed', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    let otherCalled = false;
    rig.breathEngine.subscribe(() => {
      throw new Error('boom');
    });
    rig.breathEngine.subscribe(() => {
      otherCalled = true;
    });
    rig.breathEngine.start();
    expect(otherCalled).toBe(true);
  });
});

describe('BreathEngine — custom curves', () => {
  test('curveName override applies curve', () => {
    const rig = createBreathTestRig(BOX_CONFIG, { timerMode: 'high-precision' });
    // Re-create with custom curve
    rig.breathEngine.dispose();
    const engine = new BreathEngine({
      monotonic: rig.monotonic,
      timerEngine: rig.timerEngine,
      config: BOX_CONFIG,
      curveName: 'linear',
    });
    engine.start();
    rig.clock.advance(2_000);
    const snap = engine.snapshot();
    expect(snap.depth).toBeCloseTo(0.5, 1);
    engine.dispose();
  });

  test('custom curve function is used', () => {
    const rig = createBreathTestRig(BOX_CONFIG, { timerMode: 'high-precision' });
    rig.breathEngine.dispose();
    const customCurve = (x: number): number => x * 0.5; // half-depth custom curve
    const engine = new BreathEngine({
      monotonic: rig.monotonic,
      timerEngine: rig.timerEngine,
      config: BOX_CONFIG,
      curve: customCurve,
    });
    engine.start();
    rig.clock.advance(2_000); // 50% through inhale
    expect(engine.snapshot().depth).toBeCloseTo(0.25, 1);
    engine.dispose();
  });
});

describe('BreathEngine — timer requirement', () => {
  test('throws if Timer Engine is not running on start', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.timerEngine.stop();
    expect(() => rig.breathEngine.start()).toThrow(/TimerEngine/);
  });
});

describe('BreathEngine — zero-hold configurations', () => {
  test('no-hold cycle: cycle-completed and cycle-started fire at same tick', () => {
    const rig = createBreathTestRig(NO_HOLD_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(10_001); // 1ms into cycle 1
    const completed0 = rig.breathEvents.find((e) => e.type === 'cycle-completed' && e.cycleIndex === 0);
    const started1 = rig.breathEvents.find((e) => e.type === 'cycle-started' && e.cycleIndex === 1);
    expect(completed0).toBeDefined();
    expect(started1).toBeDefined();
  });

  test('no-hold cycle: breath-completed fires when exhale ends', () => {
    const rig = createBreathTestRig(NO_HOLD_CONFIG);
    rig.breathEngine.start();
    rig.clock.advance(10_001);
    const breathCompleted = rig.breathEvents.find((e) => e.type === 'breath-completed');
    expect(breathCompleted).toBeDefined();
    if (breathCompleted && breathCompleted.type === 'breath-completed') {
      expect(breathCompleted.cycleIndex).toBe(0);
    }
  });
});

describe('BreathEngine — disposal', () => {
  test('dispose stops receiving Timer Engine events', () => {
    const rig = createBreathTestRig(BOX_CONFIG);
    rig.breathEngine.start();
    rig.breathEngine.dispose();
    const beforeCount = rig.breathEvents.length;
    rig.clock.advance(2_000);
    // No new breath events should arrive (no active session).
    // But Timer Engine still runs and emits ticks.
    expect(rig.breathEvents.length).toBe(beforeCount);
  });
});