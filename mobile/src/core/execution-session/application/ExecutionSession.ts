/**
 * ExecutionSession — the Aggregate Root for a single breathing session.
 *
 * Responsibilities (DDD aggregate):
 *   - Owns identity (SessionId, ProtocolId, ExecutionPlanId) — invariant.
 *   - Owns the frozen plan reference — never mutated, never replaced.
 *   - Owns the FSM (8 states + transitions).
 *   - Owns the event log (immutable, append-only).
 *   - Owns derived state (metrics, timeline, snapshot).
 *
 * Out of scope (forbidden by brief):
 *   - Persistence, network, storage, database.
 *   - UI, React, React Native.
 *   - Audio, animation, analytics, safety.
 *   - Subscribing to external event sources (e.g. Runtime).
 *     The Aggregate is driven by its own API only; an integration
 *     layer (Session Engine) is out of scope for Sprint 5.
 *
 * Invariants enforced here:
 *   1. Identity never changes after construction.
 *   2. Plan reference never changes after construction.
 *   3. Event log is append-only; past events are never mutated.
 *   4. State transitions follow the `legalTransitions` table.
 *   5. Snapshot version increments on every state change.
 */

import { EngineError, Err, Ok, type Result } from '@araflow/shared-contracts';

import type { ProtocolExecutionPlan } from '@core/protocol-compiler';

import type { ExecutionSessionDeps, MonotonicClock } from './ExecutionSessionDeps';
import { SessionEventLog } from './SessionEventLog';
import {
  type CycleCompletedEvent,
  type ExecutionPlanId,
  type PhaseChangedEvent,
  type SessionCancelledEvent,
  type SessionCompletedEvent,
  type SessionCreatedEvent,
  type SessionEvent,
  type SessionFailedEvent,
  type SessionInterruptedEvent,
  type SessionPausedEvent,
  type SessionPreparingEvent,
  type SessionResumedEvent,
  type SessionStartedEvent,
  type SnapshotCreatedEvent,
} from '../domain/SessionEvent';
import type { SessionMetrics } from '../domain/SessionMetrics';
import type { SessionSnapshot } from '../domain/SessionSnapshot';
import { canTransition, isTerminalSessionState, type SessionState } from '../domain/SessionState';
import type { SessionTimeline } from '../domain/SessionTimeline';
import { computeMetrics } from '../util/session-metrics';
import { buildTimeline } from '../util/session-timeline';

export class ExecutionSession {
  // --- Identity (invariant — never changes) ---
  private readonly _id: ExecutionSessionDeps['sessionId'];
  private readonly _protocolId: ExecutionSessionDeps['protocolId'];
  private readonly _planId: ExecutionSessionDeps['executionPlanId'];
  private readonly _plan: ProtocolExecutionPlan;
  private readonly clock: MonotonicClock;

  // --- Mutable runtime state (FSM + counters) ---
  private _state: SessionState = 'idle';
  private _version = 0;
  private _disposed = false;
  private _startedAtMs: number | null = null;
  private _lastPauseAtMs: number | null = null;
  private readonly log: SessionEventLog;

  constructor(deps: ExecutionSessionDeps) {
    this._id = deps.sessionId;
    this._protocolId = deps.protocolId;
    this._planId = deps.executionPlanId;
    this._plan = deps.plan;
    this.clock = deps.now ?? ((): number => Date.now());
    this.log = new SessionEventLog();

    // Session is created in 'idle' state and immediately emits
    // session-created. This anchors the log and provides the
    // first snapshot a consumer will see.
    const created: SessionCreatedEvent = Object.freeze({
      type: 'session-created',
      sessionId: this._id,
      protocolId: this._protocolId,
      executionPlanId: this._planId,
      state: 'idle',
      monotonicMs: this.clock(),
    });
    this.log.append(created);
  }

  // ========================================================================
  // Identity (read-only — invariants)
  // ========================================================================

  public sessionId = (): ExecutionSessionDeps['sessionId'] => this._id;

  public protocolId = (): ExecutionSessionDeps['protocolId'] => this._protocolId;

  public executionPlanId = (): ExecutionPlanId => this._planId;

  public plan = (): ProtocolExecutionPlan => this._plan;

  // ========================================================================
  // Lifecycle
  // ========================================================================

  /**
   * Transition idle → preparing → running.
   *
   * On first call: emits session-preparing then session-started.
   * On subsequent calls from terminal states: returns Err.
   */
  public start = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('start'));
    }
    if (this._state === 'preparing' || this._state === 'running' || this._state === 'paused') {
      // Idempotent no-op — already in flight.
      return Ok(undefined);
    }
    if (!canTransition(this._state, 'preparing')) {
      return Err(this.transitionError(this._state, 'preparing'));
    }
    this.transitionTo('preparing');
    const preparingEv: SessionPreparingEvent = Object.freeze({
      type: 'session-preparing',
      monotonicMs: this.clock(),
    });
    this.log.append(preparingEv);

    // Promoting to running — this is the canonical start.
    this.transitionTo('running');
    const now = this.clock();
    this._startedAtMs = now;
    const startedEv: SessionStartedEvent = Object.freeze({
      type: 'session-started',
      monotonicMs: now,
    });
    this.log.append(startedEv);
    return Ok(undefined);
  };

  /**
   * Transition running → paused.
   * No-op if already paused.
   */
  public pause = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('pause'));
    }
    if (this._state === 'paused') {
      return Ok(undefined);
    }
    if (!canTransition(this._state, 'paused')) {
      return Err(this.transitionError(this._state, 'paused'));
    }
    const now = this.clock();
    this._lastPauseAtMs = now;
    this.transitionTo('paused');
    const ev: SessionPausedEvent = Object.freeze({
      type: 'session-paused',
      monotonicMs: now,
      pausedForMs: 0,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Transition paused → running.
   * No-op if already running.
   */
  public resume = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('resume'));
    }
    if (this._state === 'running') {
      return Ok(undefined);
    }
    if (!canTransition(this._state, 'running')) {
      return Err(this.transitionError(this._state, 'running'));
    }
    const now = this.clock();
    const resumedFrom = this._lastPauseAtMs ?? now;
    this._lastPauseAtMs = null;
    this.transitionTo('running');
    const ev: SessionResumedEvent = Object.freeze({
      type: 'session-resumed',
      monotonicMs: now,
      resumedFromMs: resumedFrom,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Transition to 'cancelled'. Allowed from preparing/running/paused.
   * No-op from terminal states (returns Ok).
   */
  public cancel = (reason = 'user_cancelled'): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('cancel'));
    }
    if (isTerminalSessionState(this._state)) {
      return Ok(undefined);
    }
    if (!canTransition(this._state, 'cancelled')) {
      return Err(this.transitionError(this._state, 'cancelled'));
    }
    this.transitionTo('cancelled');
    const ev: SessionCancelledEvent = Object.freeze({
      type: 'session-cancelled',
      monotonicMs: this.clock(),
      reason,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Transition to 'completed'. Allowed from running.
   */
  public complete = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('complete'));
    }
    if (!canTransition(this._state, 'completed')) {
      return Err(this.transitionError(this._state, 'completed'));
    }
    this.transitionTo('completed');
    const now = this.clock();
    const totalElapsedMs = this._startedAtMs === null ? 0 : now - this._startedAtMs;
    const ev: SessionCompletedEvent = Object.freeze({
      type: 'session-completed',
      monotonicMs: now,
      totalElapsedMs,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Transition to 'failed'. Allowed from preparing/running/paused.
   */
  public fail = (code: string, message: string): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('fail'));
    }
    if (!canTransition(this._state, 'failed')) {
      return Err(this.transitionError(this._state, 'failed'));
    }
    this.transitionTo('failed');
    const ev: SessionFailedEvent = Object.freeze({
      type: 'session-failed',
      monotonicMs: this.clock(),
      code,
      message,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Transition to 'interrupted'. Allowed from running/paused.
   */
  public interrupt = (reason = 'external'): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('interrupt'));
    }
    if (!canTransition(this._state, 'interrupted')) {
      return Err(this.transitionError(this._state, 'interrupted'));
    }
    this.transitionTo('interrupted');
    const ev: SessionInterruptedEvent = Object.freeze({
      type: 'session-interrupted',
      monotonicMs: this.clock(),
      reason,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  // ========================================================================
  // Observation (drive phase / cycle tracking)
  // ========================================================================

  /**
   * Record a phase change. Updates derived metrics (currentPhase,
   * currentCycle) and appends a phase-changed event. Does NOT change
   * session state — phase tracking is independent of the FSM.
   */
  public recordPhaseChange = (input: {
    readonly phase: PhaseChangedEvent['phase'];
    readonly cycleIndex: number;
    readonly phaseIndex: number;
    readonly phaseElapsedMs: number;
    readonly phaseDurationMs: number;
    readonly monotonicMs?: number;
  }): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('recordPhaseChange'));
    }
    if (isTerminalSessionState(this._state)) {
      return Err(
        new EngineError('Cannot record phase change on a terminal session', {
          code: 'session_terminal_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }
    const ev: PhaseChangedEvent = Object.freeze({
      type: 'phase-changed',
      monotonicMs: input.monotonicMs ?? this.clock(),
      phase: input.phase,
      cycleIndex: input.cycleIndex,
      phaseIndex: input.phaseIndex,
      phaseElapsedMs: input.phaseElapsedMs,
      phaseDurationMs: input.phaseDurationMs,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  /**
   * Record a cycle completion. Updates the completedCycles counter
   * and appends a cycle-completed event. Does NOT change session state.
   */
  public recordCycleCompleted = (input: {
    readonly cycleIndex: number;
    readonly cycleElapsedMs: number;
    readonly totalCycles: number;
    readonly monotonicMs?: number;
  }): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('recordCycleCompleted'));
    }
    if (isTerminalSessionState(this._state)) {
      return Err(
        new EngineError('Cannot record cycle completion on a terminal session', {
          code: 'session_terminal_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }
    const ev: CycleCompletedEvent = Object.freeze({
      type: 'cycle-completed',
      monotonicMs: input.monotonicMs ?? this.clock(),
      cycleIndex: input.cycleIndex,
      cycleElapsedMs: input.cycleElapsedMs,
      totalCycles: input.totalCycles,
    });
    this.log.append(ev);
    return Ok(undefined);
  };

  // ========================================================================
  // Read models
  // ========================================================================

  public state = (): SessionState => this._state;

  public version = (): number => this._version;

  public isDisposed = (): boolean => this._disposed;

  public snapshot = (): SessionSnapshot => {
    const metrics = this.metrics();
    const snapshot: SessionSnapshot = Object.freeze({
      sessionId: this._id,
      protocolId: this._protocolId,
      executionPlanId: this._planId,
      state: this._state,
      elapsedMs: metrics.elapsedMs,
      remainingMs: metrics.remainingMs,
      currentPhase: metrics.currentPhase,
      currentCycle: metrics.currentCycle,
      progress: metrics.progress,
      metrics,
      timestamp: this.clock(),
      version: this._version,
    });

    // snapshot-created is a derived event — appended after the snapshot
    // is taken so the version in the snapshot matches the log.
    const ev: SnapshotCreatedEvent = Object.freeze({
      type: 'snapshot-created',
      monotonicMs: snapshot.timestamp,
      version: this._version,
    });
    this.log.append(ev);
    return snapshot;
  };

  public metrics = (): SessionMetrics =>
    computeMetrics({
      events: this.log.all(),
      plannedDurationMs: this._plan.totalDuration as unknown as number,
      nowMs: this.clock(),
    });

  public timeline = (): SessionTimeline => buildTimeline(this.log.all());

  public events = (): readonly SessionEvent[] => this.log.all();

  // ========================================================================
  // Disposal
  // ========================================================================

  public dispose = (): void => {
    if (this._disposed) {
      return;
    }
    this._disposed = true;
    this.log.clear();
  };

  // ========================================================================
  // Internal
  // ========================================================================

  private transitionTo(next: SessionState): void {
    if (!canTransition(this._state, next) && !(this._state === 'idle' && next === 'preparing')) {
      // Defensive — should be caught by caller, but enforce here too.
      throw new Error(`Illegal session transition: ${this._state} → ${next}`);
    }
    this._state = next;
    this._version += 1;
  }

  private transitionError(from: SessionState, to: SessionState): EngineError {
    return new EngineError(`Illegal session transition: ${from} → ${to}`, {
      code: 'session_invalid_transition',
      severity: 'error',
      context: { from, to },
    });
  }

  private disposedError(op: string): EngineError {
    return new EngineError(`Cannot ${op} a disposed session`, {
      code: 'session_disposed',
      severity: 'error',
      context: { state: this._state },
    });
  }
}
