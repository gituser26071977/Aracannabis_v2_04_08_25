/**
 * Test fixtures for Session Orchestrator tests.
 */

import type { BreathPhase, ProtocolId, SessionId } from '@araflow/shared-contracts';

import { ExecutionPlanId, type SessionEvent } from '@core/execution-session';
import type {
  RuntimeEngine,
  RuntimeEvent,
  RuntimeEventListener,
  RuntimeState,
  RuntimeUnsubscribe,
} from '@core/runtime';

// =============================================================================
// FakeRuntime — minimal RuntimeEngine double
// =============================================================================

export class FakeRuntime implements Pick<RuntimeEngine, 'subscribe' | 'getState'> {
  private readonly listeners = new Set<RuntimeEventListener>();
  private _state: RuntimeState = 'uninitialized';

  public subscribe = (listener: RuntimeEventListener): RuntimeUnsubscribe => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  public emit = (event: RuntimeEvent): void => {
    for (const listener of [...this.listeners]) {
      listener(event);
    }
  };

  public getState = (): RuntimeState => this._state;

  public setState = (state: RuntimeState): void => {
    this._state = state;
  };

  public listenerCount = (): number => this.listeners.size;
}

// =============================================================================
// Runtime event builders
// =============================================================================

export const runtimeEvent = {
  started: (): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-started',
      executionId: '01HXYZ00000000000000000000' as never,
      monotonicMs: 100,
    },
  }),
  paused: (monotonicMs = 110): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-paused',
      executionId: '01HXYZ00000000000000000000' as never,
      atElapsedMs: 10,
      monotonicMs,
    },
  }),
  resumed: (monotonicMs = 120): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-resumed',
      executionId: '01HXYZ00000000000000000000' as never,
      pausedForMs: 10,
      monotonicMs,
    },
  }),
  phaseChanged: (
    monotonicMs = 130,
    phase: BreathPhase = 'inhaling',
    cycleIndex = 0,
  ): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-phase-changed',
      executionId: '01HXYZ00000000000000000000' as never,
      previousPhase: null,
      currentPhase: phase,
      cycleIndex,
      phaseProgress: 0,
      monotonicMs,
    },
  }),
  cycleCompleted: (monotonicMs = 140, cycleIndex = 0): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-cycle-completed',
      executionId: '01HXYZ00000000000000000000' as never,
      cycleIndex,
      monotonicMs,
    },
  }),
  completed: (monotonicMs = 200): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-completed',
      executionId: '01HXYZ00000000000000000000' as never,
      totalElapsedMs: 100,
      monotonicMs,
    },
  }),
  stoppedCancelled: (monotonicMs = 200): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-stopped',
      executionId: '01HXYZ00000000000000000000' as never,
      reason: 'cancelled',
      monotonicMs,
    },
  }),
  stoppedErrored: (monotonicMs = 200): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-stopped',
      executionId: '01HXYZ00000000000000000000' as never,
      reason: 'errored',
      monotonicMs,
    },
  }),
  errored: (monotonicMs = 200, code = 'engine_error', message = 'failed'): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-errored',
      executionId: '01HXYZ00000000000000000000' as never,
      code,
      message,
      monotonicMs,
    },
  }),
  tick: (monotonicMs = 150): RuntimeEvent => ({
    source: 'protocol',
    payload: {
      type: 'protocol-runtime-tick',
      executionId: '01HXYZ00000000000000000000' as never,
      elapsedMs: 50,
      cycleIndex: 0,
      phaseIndex: 0,
      phase: 'inhaling',
      phaseProgress: 0.5,
      monotonicMs,
    },
  }),
  timerTick: (): RuntimeEvent => ({
    source: 'timer',
    payload: {
      type: 'tick',
      monotonicMs: 100,
      wallIso: '2026-06-30T00:00:00.000Z',
      tickIndex: 1,
      elapsedMs: 100,
      totalElapsedMs: 100,
    } as never,
  }),
  breathPhaseChanged: (): RuntimeEvent => ({
    source: 'breath',
    payload: {
      type: 'phase-changed',
      monotonicMs: 100,
      wallIso: '2026-06-30T00:00:00.000Z',
      previousPhase: null,
      currentPhase: 'inhaling',
      cycleIndex: 0,
      phaseProgress: 0,
    } as never,
  }),
  runtimeCompileFailed: (monotonicMs = 50): RuntimeEvent => ({
    source: 'runtime',
    payload: {
      type: 'runtime-compile-failed',
      failures: [],
      warnings: [],
      monotonicMs,
    },
  }),
  runtimeError: (monotonicMs = 60, code = 'rt_error', message = 'rt failed'): RuntimeEvent => ({
    source: 'runtime',
    payload: {
      type: 'runtime-error',
      code,
      message,
      monotonicMs,
    },
  }),
  runtimeCompleted: (monotonicMs = 250): RuntimeEvent => ({
    source: 'runtime',
    payload: {
      type: 'runtime-completed',
      totalElapsedMs: 200,
      monotonicMs,
    },
  }),
  runtimeDisposed: (monotonicMs = 300): RuntimeEvent => ({
    source: 'runtime',
    payload: {
      type: 'runtime-disposed',
      monotonicMs,
    },
  }),
  runtimeWarnings: (monotonicMs = 25): RuntimeEvent => ({
    source: 'runtime',
    payload: {
      type: 'runtime-warnings',
      warnings: [],
      monotonicMs,
    },
  }),
};

// =============================================================================
// Anchor (session-created) for replays
// =============================================================================

export const anchorSessionCreated = (
  sessionId: SessionId = '01ARZ3NDEKTSV4RRFFQ69G5F01' as SessionId,
  protocolId: ProtocolId = '01ARZ3NDEKTSV4RRFFQ69G5FAV' as ProtocolId,
  executionPlanId: ExecutionPlanId = ExecutionPlanId('01HXYZ00000000000000000000'),
  monotonicMs = 0,
): SessionEvent =>
  Object.freeze({
    type: 'session-created',
    sessionId,
    protocolId,
    executionPlanId,
    state: 'idle',
    monotonicMs,
  });
