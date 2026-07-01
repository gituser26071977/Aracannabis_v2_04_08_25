/**
 * Test helpers for the Animation Engine module.
 *
 * The Engine depends on RuntimeEngine, BreathEngine, TimerEngine, and
 * ExecutionSession. Real instances are expensive; we provide thin
 * fakes that implement the public APIs the Engine actually uses.
 */

import type { BreathPhase } from '@core/breath-engine';
import type {
  RuntimeEngine,
  RuntimeEvent,
  RuntimeEventListener,
  RuntimeUnsubscribe,
} from '@core/runtime';
import type { TimerEvent } from '@core/timer-engine';

// REDACTED
// Fake Runtime
// REDACTED

export interface FakeRuntime extends RuntimeEngine {
  emit(event: RuntimeEvent): void;
  listenerCount(): number;
}

export const buildFakeRuntime = (): FakeRuntime => {
  const listeners = new Set<RuntimeEventListener>();
  const runtime = {
    subscribe(listener: RuntimeEventListener): RuntimeUnsubscribe {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getState: () => 'running' as never,
    getMetrics: () => ({}) as never,
    getSnapshot: () => ({}) as never,
    getExecutionPlan: () => null,
    getWarnings: () => [],
    emit(event: RuntimeEvent): void {
      for (const l of Array.from(listeners)) {
        l(event);
      }
    },
    listenerCount(): number {
      return listeners.size;
    },
  } as unknown as FakeRuntime;
  return runtime;
};

// REDACTED
// Runtime event builders
// REDACTED

export const runtimeEvent = {
  started: (monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-started',
      executionId: 'exec-1',
      monotonicMs,
    },
  }),
  paused: (monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-paused',
      executionId: 'exec-1',
      atElapsedMs: 0,
      monotonicMs,
    },
  }),
  resumed: (monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-resumed',
      executionId: 'exec-1',
      pausedForMs: 0,
      monotonicMs,
    },
  }),
  phaseChanged: (currentPhase: BreathPhase, monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-phase-changed',
      executionId: 'exec-1',
      previousPhase: null,
      currentPhase,
      cycleIndex: 0,
      phaseProgress: 0,
      monotonicMs,
    },
  }),
  cycleCompleted: (cycleIndex = 0, monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-cycle-completed',
      executionId: 'exec-1',
      cycleIndex,
      monotonicMs,
    },
  }),
  completed: (totalElapsedMs = 0, monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-completed',
      executionId: 'exec-1',
      totalElapsedMs,
      monotonicMs,
    },
  }),
  stopped: (
    reason: 'completed' | 'cancelled' | 'errored' = 'cancelled',
    monotonicMs = 0,
  ): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-stopped',
      executionId: 'exec-1',
      reason,
      monotonicMs,
    },
  }),
  errored: (monotonicMs = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-errored',
      executionId: 'exec-1',
      code: 'test_error',
      message: 'fake',
      monotonicMs,
    },
  }),
};

// REDACTED
// Fake Timer
// REDACTED

export interface FakeTimer {
  subscribe(listener: (event: TimerEvent) => void): () => void;
  emit(event: TimerEvent): void;
}

export const buildFakeTimer = (): FakeTimer => {
  const listeners = new Set<(event: TimerEvent) => void>();
  return {
    subscribe(listener: (event: TimerEvent) => void): () => void {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    emit(event: TimerEvent): void {
      for (const l of Array.from(listeners)) {
        l(event);
      }
    },
  } as unknown as FakeTimer;
};

export const timerEvent = {
  tick: (monotonicMs = 0): TimerEvent =>
    ({
      type: 'tick',
      monotonicMs,
      tickIndex: 0,
      elapsedMs: monotonicMs,
      totalElapsedMs: monotonicMs,
    }) as TimerEvent,
};

// REDACTED
// Fake Breath Engine
// REDACTED

export interface FakeBreath {
  subscribe(
    listener: (event: { type: string; phase?: BreathPhase; phaseDurationMs?: number }) => void,
  ): () => void;
  emit(event: { type: string; phase?: BreathPhase; phaseDurationMs?: number }): void;
}

export const buildFakeBreath = (): FakeBreath => {
  const listeners = new Set<
    (event: { type: string; phase?: BreathPhase; phaseDurationMs?: number }) => void
  >();
  return {
    subscribe(
      listener: (event: { type: string; phase?: BreathPhase; phaseDurationMs?: number }) => void,
    ): () => void {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    emit(event: { type: string; phase?: BreathPhase; phaseDurationMs?: number }): void {
      for (const l of Array.from(listeners)) {
        l(event);
      }
    },
  } as unknown as FakeBreath;
};

export const breathEvent = {
  phaseChanged: (phase: BreathPhase, phaseDurationMs = 1000) => ({
    type: 'breath-phase-changed',
    phase,
    phaseDurationMs,
  }),
};

// REDACTED
// Fake ExecutionSession
// REDACTED

export interface FakeSession {
  plan(): { phases: ReadonlyArray<{ phase: BreathPhase; duration: number }> } | null;
}

export const buildFakeSession = (
  phases: ReadonlyArray<{ phase: BreathPhase; duration: number }>,
): FakeSession => ({
  plan: () => ({ phases }),
});

export const sessionSnapshotWithNoPhases = (): FakeSession => ({
  plan: () => null,
});
