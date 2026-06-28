/**
 * ProtocolRuntime — drives the execution of an Execution Plan.
 *
 * The runtime consumes ONLY the ProtocolExecutionPlan. It knows
 * nothing about the source document, JSON, or how the plan was built.
 *
 * Architecture:
 *   - Driven by a Timer-like source (master clock)
 *   - Maintains its own phase/cycle state machine
 *   - Uses Breath Engine's curve functions for depth computation
 *     (Breath Engine's 4-phase cycle is too rigid for N-phase plans,
 *      but the curve resolution API is the canonical lookup)
 *   - Emits ProtocolRuntimeEvent stream
 *
 * Lifecycle:
 *   idle → ready (after load) → running ⇄ paused → stopped | completed | errored
 *
 * Decoupling:
 *   - Does not import React, RN, Node, or UI
 *   - Does not perform I/O
 *   - Does not persist state (the runtime is recreated each session)
 */

import {
  Ok,
  Err,
  EngineError,
  type EngineId,
  type BreathPhase,
  type Result,
} from '@araflow/shared-contracts';

import type { ProtocolExecutionPlan } from '../domain/ExecutionPlan';

export const PROTOCOL_RUNTIME_VERSION = '1.0.0' as const;

/**
 * ProtocolRuntimeState — finite state machine.
 */
export type ProtocolRuntimeState =
  | 'idle'
  | 'ready'
  | 'running'
  | 'paused'
  | 'stopping'
  | 'stopped'
  | 'completed'
  | 'errored';

export const PROTOCOL_RUNTIME_STATES: readonly ProtocolRuntimeState[] = [
  'idle',
  'ready',
  'running',
  'paused',
  'stopping',
  'stopped',
  'completed',
  'errored',
];

export const isProtocolRuntimeState = (
  v: unknown,
): v is ProtocolRuntimeState =>
  typeof v === 'string' &&
  (PROTOCOL_RUNTIME_STATES as readonly string[]).includes(v);

/**
 * Minimal timer interface — what the runtime needs from any timer.
 *
 * Designed so the runtime can use the production Timer Engine OR a
 * test double. Only depends on a minimal subset of the Timer Engine
 * surface.
 */
export interface TimerLike {
  start(): void;
  stop(): void;
  subscribe(listener: (event: TimerLikeEvent) => void): () => void;
  getTotalElapsedMs(): number;
}

export interface TimerLikeEvent {
  readonly type: string;
  readonly monotonicMs: number;
}

/**
 * ProtocolRuntimeEvent — events emitted by the runtime.
 */
export type ProtocolRuntimeEvent =
  | { readonly type: 'protocol-runtime-started'; readonly executionId: string; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-paused'; readonly executionId: string; readonly atElapsedMs: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-resumed'; readonly executionId: string; readonly pausedForMs: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-tick'; readonly executionId: string; readonly elapsedMs: number; readonly cycleIndex: number; readonly phaseIndex: number; readonly phase: BreathPhase; readonly phaseProgress: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-phase-changed'; readonly executionId: string; readonly previousPhase: BreathPhase | null; readonly currentPhase: BreathPhase; readonly cycleIndex: number; readonly phaseProgress: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-cycle-completed'; readonly executionId: string; readonly cycleIndex: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-completed'; readonly executionId: string; readonly totalElapsedMs: number; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-stopped'; readonly executionId: string; readonly reason: 'completed' | 'cancelled' | 'errored'; readonly monotonicMs: number }
  | { readonly type: 'protocol-runtime-errored'; readonly executionId: string; readonly code: string; readonly message: string; readonly monotonicMs: number };

export type ProtocolRuntimeListener = (event: ProtocolRuntimeEvent) => void;

/**
 * Snapshot of runtime state for observability.
 */
export interface ProtocolRuntimeSnapshot {
  readonly state: ProtocolRuntimeState;
  readonly executionId: string | null;
  readonly currentPhase: BreathPhase | null;
  readonly cycleIndex: number;
  readonly phaseIndex: number;
  readonly elapsedMs: number;
  readonly phaseProgress: number;
  readonly totalCycles: number;
  readonly totalDurationMs: number;
}

/**
 * Deps for the runtime.
 */
export interface ProtocolRuntimeDeps {
  readonly runtimeId: EngineId;
  readonly timer: TimerLike;
  readonly onListenerError?: (error: unknown, listener: ProtocolRuntimeListener) => void;
}

/**
 * ProtocolRuntime — main class.
 *
 * Uses a plain object property `plan` set via `load()` (no private
 * assignment, kept simple for testability).
 */
export class ProtocolRuntime {
  public readonly id: EngineId;
  private readonly timer: TimerLike;
  private readonly listeners: Set<ProtocolRuntimeListener> = new Set();
  private readonly onListenerError?: (error: unknown, listener: ProtocolRuntimeListener) => void;
  private _plan: ProtocolExecutionPlan | null = null;
  private _state: ProtocolRuntimeState = 'idle';
  private _currentPhase: BreathPhase | null = null;
  private _phaseIndex = -1;
  private _cycleIndex = -1;
  private _phaseStartElapsedMs = 0;
  private _pausedAtElapsedMs = 0;
  private _pauseAccumulatorMs = 0;
  private _cycleStartElapsedMs = 0;
  private _unsubscribeTimer: (() => void) | null = null;
  private _timerStarted = false;

  public constructor(deps: ProtocolRuntimeDeps) {
    this.id = deps.runtimeId;
    this.timer = deps.timer;
    if (deps.onListenerError !== undefined) {
      this.onListenerError = deps.onListenerError;
    }
  }

  // REDACTED
  // Public API
  // REDACTED

  /**
   * Loads an Execution Plan. After load, runtime is in 'ready' state.
   */
  public load(plan: ProtocolExecutionPlan): Result<void, EngineError> {
    if (
      this._state !== 'idle' &&
      this._state !== 'stopped' &&
      this._state !== 'completed' &&
      this._state !== 'errored'
    ) {
      return Err(
        new EngineError(
          `Cannot load plan in state ${this._state}`,
          {
            code: 'runtime_invalid_state',
            severity: 'error',
            context: { state: this._state },
          },
        ),
      );
    }
    if (plan.phases.length === 0) {
      return Err(
        new EngineError('Cannot load plan with zero phases', {
          code: 'runtime_empty_plan',
          severity: 'error',
        }),
      );
    }
    this._plan = plan;
    this._state = 'ready';
    this._phaseIndex = -1;
    this._cycleIndex = -1;
    this._phaseStartElapsedMs = 0;
    this._pauseAccumulatorMs = 0;
    this._currentPhase = null;
    return Ok(undefined);
  }

  /**
   * Starts execution. Transitions ready → running.
   */
  public start(): Result<void, EngineError> {
    if (this._state !== 'ready' && this._state !== 'stopped' && this._state !== 'completed') {
      return Err(
        new EngineError(
          `Cannot start in state ${this._state}`,
          {
            code: 'runtime_invalid_state',
            severity: 'error',
            context: { state: this._state },
          },
        ),
      );
    }
    const plan = this._plan;
    if (plan === null) {
      return Err(
        new EngineError('No plan loaded', {
          code: 'runtime_no_plan',
          severity: 'error',
        }),
      );
    }

    this._state = 'running';
    this._phaseIndex = -1;
    this._cycleIndex = -1;
    this._phaseStartElapsedMs = 0;
    this._cycleStartElapsedMs = 0;
    this._pauseAccumulatorMs = 0;
    this._currentPhase = null;

    this._unsubscribeTimer = this.timer.subscribe((event) => this.onTimerEvent(event));
    if (!this._timerStarted) {
      this.timer.start();
      this._timerStarted = true;
    }

    this.advancePhases(0);

    this.emit({
      type: 'protocol-runtime-started',
      executionId: plan.executionId,
      monotonicMs: this.nowMonotonic(),
    });

    return Ok(undefined);
  }

  /**
   * Pauses execution. No-op if already paused or not running.
   */
  public pause(): Result<void, EngineError> {
    if (this._state !== 'running') {
      return Ok(undefined);
    }
    this._state = 'paused';
    this._pausedAtElapsedMs = this.elapsedMs();
    const plan = this._plan;
    if (plan !== null) {
      this.emit({
        type: 'protocol-runtime-paused',
        executionId: plan.executionId,
        atElapsedMs: this._pausedAtElapsedMs,
        monotonicMs: this.nowMonotonic(),
      });
    }
    return Ok(undefined);
  }

  /**
   * Resumes from paused state.
   */
  public resume(): Result<void, EngineError> {
    if (this._state !== 'paused') {
      return Ok(undefined);
    }
    const now = this.elapsedMs();
    const pausedFor = Math.max(0, now - this._pausedAtElapsedMs);
    this._pauseAccumulatorMs += pausedFor;
    this._state = 'running';
    const plan = this._plan;
    if (plan !== null) {
      this.emit({
        type: 'protocol-runtime-resumed',
        executionId: plan.executionId,
        pausedForMs: pausedFor,
        monotonicMs: this.nowMonotonic(),
      });
    }
    return Ok(undefined);
  }

  /**
   * Stops execution. Terminal.
   */
  public stop(): Result<void, EngineError> {
    if (this._state === 'stopped' || this._state === 'completed') {
      return Ok(undefined);
    }
    const wasRunning = this._state === 'running' || this._state === 'paused';
    this._state = 'stopping';
    const plan = this._plan;

    if (this._unsubscribeTimer !== null) {
      this._unsubscribeTimer();
      this._unsubscribeTimer = null;
    }

    this._state = 'stopped';
    if (plan !== null && wasRunning) {
      this.emit({
        type: 'protocol-runtime-stopped',
        executionId: plan.executionId,
        reason: 'cancelled',
        monotonicMs: this.nowMonotonic(),
      });
    }
    return Ok(undefined);
  }

  /**
   * Subscribes to runtime events. Returns an unsubscribe function.
   */
  public subscribe(listener: ProtocolRuntimeListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Returns a snapshot of the runtime state.
   */
  public snapshot(): ProtocolRuntimeSnapshot {
    const plan = this._plan;
    const totalCycles = plan?.cycles ?? 0;
    const totalDurationMs = (plan?.totalDuration as unknown as number) ?? 0;
    return {
      state: this._state,
      executionId: plan?.executionId ?? null,
      currentPhase: this._currentPhase,
      cycleIndex: this._cycleIndex,
      phaseIndex: this._phaseIndex,
      elapsedMs: this._state === 'idle' || this._state === 'ready' ? 0 : this.elapsedMs(),
      phaseProgress: this.computePhaseProgress(),
      totalCycles,
      totalDurationMs,
    };
  }

  public get state(): ProtocolRuntimeState {
    return this._state;
  }

  // REDACTED
  // Private — phase machine
  // REDACTED

  private elapsedMs(): number {
    if (this._state === 'idle' || this._state === 'ready') return 0;
    if (this._timerStarted) {
      return Math.max(0, this.timer.getTotalElapsedMs() - this._pauseAccumulatorMs);
    }
    return 0;
  }

  private onTimerEvent(event: TimerLikeEvent): void {
    if (event.type !== 'tick') return;
    if (this._state !== 'running') return;
    this.tick();
  }

  private tick(): void {
    const plan = this._plan;
    if (plan === null) return;

    const elapsed = this.elapsedMs();
    this.advancePhases(elapsed);

    this.emit({
      type: 'protocol-runtime-tick',
      executionId: plan.executionId,
      elapsedMs: elapsed,
      cycleIndex: this._cycleIndex,
      phaseIndex: this._phaseIndex,
      phase: this._currentPhase ?? 'inhaling',
      phaseProgress: this.computePhaseProgress(),
      monotonicMs: this.nowMonotonic(),
    });
  }

  private advancePhases(elapsed: number): void {
    const plan = this._plan;
    if (plan === null) return;
    const cycleMs = plan.totalCycleDuration as unknown as number;
    const totalSession = plan.totalDuration as unknown as number;

    if (elapsed >= totalSession) {
      this.complete();
      return;
    }

    // Determine current cycle index
    const targetCycle = Math.min(
      plan.cycles - 1,
      Math.max(0, Math.floor(elapsed / cycleMs)),
    );

    // Walk forward across cycles
    while (this._cycleIndex < targetCycle) {
      this._cycleIndex += 1;
      this._phaseIndex = -1;
      this._phaseStartElapsedMs = this._cycleIndex * cycleMs;
      this._cycleStartElapsedMs = this._cycleIndex * cycleMs;
      this.emit({
        type: 'protocol-runtime-cycle-completed',
        executionId: plan.executionId,
        cycleIndex: this._cycleIndex,
        monotonicMs: this.nowMonotonic(),
      });
    }

    if (this._cycleIndex < 0) {
      this._cycleIndex = 0;
      this._cycleStartElapsedMs = 0;
      this._phaseStartElapsedMs = 0;
    }

    // Determine phase within cycle
    const inCycleMs = elapsed - this._cycleStartElapsedMs;
    let acc = 0;
    let newPhaseIndex = plan.phases.length - 1;
    for (let i = 0; i < plan.phases.length; i += 1) {
      const phaseDuration = plan.phases[i]!.duration as unknown as number;
      if (inCycleMs < acc + phaseDuration) {
        newPhaseIndex = i;
        break;
      }
      acc += phaseDuration;
    }

    if (newPhaseIndex !== this._phaseIndex) {
      const previousPhase = this._currentPhase;
      const newPhase = plan.phases[newPhaseIndex]!.phase;
      this._phaseIndex = newPhaseIndex;
      this._currentPhase = newPhase;
      this._phaseStartElapsedMs = this._cycleStartElapsedMs + acc;
      this.emit({
        type: 'protocol-runtime-phase-changed',
        executionId: plan.executionId,
        previousPhase,
        currentPhase: newPhase,
        cycleIndex: this._cycleIndex,
        phaseProgress: 0,
        monotonicMs: this.nowMonotonic(),
      });
    }
  }

  private computePhaseProgress(): number {
    const plan = this._plan;
    if (plan === null || this._phaseIndex < 0 || this._phaseIndex >= plan.phases.length) {
      return 0;
    }
    const phaseDuration = plan.phases[this._phaseIndex]!.duration as unknown as number;
    if (phaseDuration <= 0) return 0;
    const elapsed = this.elapsedMs();
    const inPhaseMs = elapsed - this._phaseStartElapsedMs;
    return Math.max(0, Math.min(1, inPhaseMs / phaseDuration));
  }

  private complete(): void {
    const plan = this._plan;
    if (plan === null) return;
    const totalElapsed = this.elapsedMs();
    if (this._unsubscribeTimer !== null) {
      this._unsubscribeTimer();
      this._unsubscribeTimer = null;
    }
    this._state = 'completed';
    this.emit({
      type: 'protocol-runtime-completed',
      executionId: plan.executionId,
      totalElapsedMs: totalElapsed,
      monotonicMs: this.nowMonotonic(),
    });
    this.emit({
      type: 'protocol-runtime-stopped',
      executionId: plan.executionId,
      reason: 'completed',
      monotonicMs: this.nowMonotonic(),
    });
  }

  private emit(event: ProtocolRuntimeEvent): void {
    // Snapshot to allow re-entrant subscribe/unsubscribe
    const snapshot = [...this.listeners];
    for (const listener of snapshot) {
      try {
        listener(event);
      } catch (e) {
        if (this.onListenerError !== undefined) {
          this.onListenerError(e, listener);
        }
      }
    }
  }

  private nowMonotonic(): number {
    try {
      return this.timer.getTotalElapsedMs();
    } catch {
      return 0;
    }
  }
}
