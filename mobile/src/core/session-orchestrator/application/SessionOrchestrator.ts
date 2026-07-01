/**
 * SessionOrchestrator — the bridge between Runtime and Execution Session.
 *
 * Responsibilities:
 *   - connect Runtime and Execution Session
 *   - consume events from Runtime
 *   - update the Session by translating Runtime events to Session API calls
 *   - maintain synchronization (detect divergence)
 *   - detect inconsistencies (out-of-order, impossible-state, invalid cycle/phase)
 *   - publish consolidated state via its own event stream
 *   - support replay of a recorded event log into a Session
 *   - integrate with SessionRecorder for in-memory recording
 *
 * Out of scope (forbidden by brief):
 *   - Persistence, storage, database.
 *   - Backend, API, network.
 *   - UI, React, React Native.
 *   - Audio, animation, analytics, safety.
 *
 * Invariants:
 *   1. The Orchestrator holds at most one active Runtime subscription.
 *   2. Replay is idempotent on a fresh Session: same recording → same state.
 *   3. Inconsistency reports are append-only.
 *   4. The Orchestrator FSM moves only through legal transitions.
 */

import {
  EngineError,
  Err,
  type Failure,
  Ok,
  type ProtocolId,
  type Result,
  type SessionId,
  type BreathPhase,
} from '@araflow/shared-contracts';

import {
  ExecutionSession,
  type SessionEvent,
  type SessionSnapshot,
  type SessionState,
} from '@core/execution-session';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import type { RuntimeEngine, RuntimeEvent, RuntimeState, RuntimeUnsubscribe } from '@core/runtime';

import {
  createOrchestratorEventStream,
  type OrchestratorEventStream,
} from './OrchestratorEventStream';
import type { SessionOrchestratorDeps } from './SessionOrchestratorDeps';
import type { SessionRecorder } from './SessionRecorder';
import type { InconsistencyReport } from '../domain/InconsistencyReport';
import { EMPTY_INCONSISTENCY_REPORTS } from '../domain/InconsistencyReport';
import type {
  OrchestratorEvent,
  OrchestratorEventListener,
  OrchestratorUnsubscribe,
} from '../domain/OrchestratorEvent';
import {
  computeOrchestratorMetrics,
  type OrchestratorMetrics,
} from '../domain/OrchestratorMetrics';
import {
  canOrchestratorTransition,
  isTerminalOrchestratorState,
  type OrchestratorState,
} from '../domain/OrchestratorState';
import type { SessionRecording } from '../domain/SessionRecording';
import { runConsistencyChecks } from '../util/consistency-checks';
import { translateRuntimeEvent, type SessionAction } from '../util/event-translator';
import { replayInto } from '../util/replay-reducer';

export class SessionOrchestrator {
  // --- Dependencies ---
  private readonly runtime: RuntimeEngine;
  private readonly session: ExecutionSession;
  private readonly clock: () => number;

  // --- FSM ---
  private _state: OrchestratorState = 'detached';
  private _disposed = false;

  // --- Event plumbing ---
  private readonly stream: OrchestratorEventStream;
  private runtimeUnsubscribe: RuntimeUnsubscribe | null = null;

  // --- Counters ---
  private _eventsProcessed = 0;
  private _eventsSkipped = 0;
  private _replays = 0;
  private reports: readonly InconsistencyReport[] = EMPTY_INCONSISTENCY_REPORTS;
  private lastSeenMonotonicMs = 0;

  // --- Recorders (attached by user) ---
  private recorders: readonly SessionRecorder[] = Object.freeze([]);

  constructor(deps: SessionOrchestratorDeps) {
    this.runtime = deps.runtime;
    this.session = deps.session;
    this.clock = deps.now ?? ((): number => Date.now());
    this.stream = createOrchestratorEventStream(deps.onListenerError);
  }

  // ========================================================================
  // Identity
  // ========================================================================

  public sessionId = (): SessionId => this.session.sessionId();
  public protocolId = (): ProtocolId => this.session.protocolId();
  public runtimeEngineId = (): string =>
    String(this.runtime.getState() === 'uninitialized' ? 'rt-uninitialized' : 'rt');

  // ========================================================================
  // FSM
  // ========================================================================

  public state = (): OrchestratorState => this._state;
  public isDisposed = (): boolean => this._disposed;

  private transitionTo(next: OrchestratorState): void {
    if (!canOrchestratorTransition(this._state, next)) {
      throw new Error(`Illegal orchestrator transition: ${this._state} → ${next}`);
    }
    this._state = next;
  }

  // ========================================================================
  // Bridge: attach / detach
  // ========================================================================

  public attach = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('attach'));
    }
    if (this._state === 'attached') {
      return Ok(undefined);
    }
    if (!canOrchestratorTransition(this._state, 'attached')) {
      return Err(
        new EngineError(`Cannot attach in state ${this._state}`, {
          code: 'orchestrator_invalid_transition',
          severity: 'error',
          context: { from: this._state, to: 'attached' },
        }),
      );
    }
    this.runtimeUnsubscribe = this.runtime.subscribe(this.onRuntimeEvent);
    this.transitionTo('attached');
    this.emit({
      type: 'orchestrator-attached',
      monotonicMs: this.clock(),
      orchestratorState: this._state,
    });
    return Ok(undefined);
  };

  public detach = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('detach'));
    }
    if (this._state === 'detached') {
      return Ok(undefined);
    }
    if (this.runtimeUnsubscribe !== null) {
      this.runtimeUnsubscribe();
      this.runtimeUnsubscribe = null;
    }
    this.transitionTo('detached');
    this.emit({
      type: 'orchestrator-detached',
      monotonicMs: this.clock(),
      orchestratorState: this._state,
    });
    return Ok(undefined);
  };

  // ========================================================================
  // Recorder integration
  // ========================================================================

  public attachRecorder = (recorder: SessionRecorder): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('attachRecorder'));
    }
    if (this.recorders.includes(recorder)) {
      return Ok(undefined);
    }
    this.recorders = Object.freeze([...this.recorders, recorder]);
    return Ok(undefined);
  };

  public detachRecorder = (recorder: SessionRecorder): Result<void, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('detachRecorder'));
    }
    this.recorders = Object.freeze(this.recorders.filter((r) => r !== recorder));
    return Ok(undefined);
  };

  public recorders_ = (): readonly SessionRecorder[] => this.recorders;

  // ========================================================================
  // Replay
  // ========================================================================

  /**
   * Drive the existing Session through the provided events. The Session
   * is mutated (its event log grows) but the orchestrator's identity
   * invariants are not violated. Returns Err if the Session's identity
   * does not match the anchor event's sessionId.
   */
  public replay = (
    events: readonly SessionEvent[],
    plan?: ProtocolExecutionPlan,
  ): Result<ExecutionSession, EngineError> => {
    if (this._disposed) {
      return Err(this.disposedError('replay'));
    }

    // Build a minimal recording from the events.
    if (events.length === 0) {
      return Err(
        new EngineError('Cannot replay an empty event list', {
          code: 'orchestrator_replay_empty',
          severity: 'error',
        }),
      );
    }
    const anchor = events[0];
    if (anchor === undefined || anchor.type !== 'session-created') {
      return Err(
        new EngineError('Replay events must begin with session-created', {
          code: 'orchestrator_replay_missing_anchor',
          severity: 'error',
        }),
      );
    }

    if (plan !== undefined) {
      // Construct a fresh Session from the recording identity + plan.
      const fresh = new ExecutionSession({
        sessionId: anchor.sessionId,
        protocolId: anchor.protocolId,
        executionPlanId: anchor.executionPlanId,
        plan,
        ...(this.clock === undefined ? {} : { now: this.clock }),
      });
      const recording: SessionRecording = Object.freeze({
        version: 1,
        sessionId: anchor.sessionId,
        protocolId: anchor.protocolId,
        executionPlanId: anchor.executionPlanId,
        recordedAtMonotonicMs: this.clock(),
        eventCount: events.length,
        events: Object.freeze(events.slice()),
      });
      const r = replayInto({ session: fresh, recording });
      if (!r.ok) {
        return r;
      }
      this._replays += 1;
      this.emit({
        type: 'orchestrator-replayed',
        monotonicMs: this.clock(),
        eventsReplayed: events.length,
        targetSessionId: anchor.sessionId,
      });
      return Ok(fresh);
    }

    // Drive the existing session.
    const recording: SessionRecording = Object.freeze({
      version: 1,
      sessionId: anchor.sessionId,
      protocolId: anchor.protocolId,
      executionPlanId: anchor.executionPlanId,
      recordedAtMonotonicMs: this.clock(),
      eventCount: events.length,
      events: Object.freeze(events.slice()),
    });
    const r = replayInto({ session: this.session, recording });
    if (!r.ok) {
      return r;
    }
    this._replays += 1;
    this.emit({
      type: 'orchestrator-replayed',
      monotonicMs: this.clock(),
      eventsReplayed: events.length,
      targetSessionId: anchor.sessionId,
    });
    return Ok(this.session);
  };

  /**
   * Static helper: construct a fresh ExecutionSession from a recording
   * + plan. Pure / deterministic.
   */
  public static replayIntoSession = (input: {
    readonly recording: SessionRecording;
    readonly plan: ProtocolExecutionPlan;
    readonly now?: () => number;
  }): Result<ExecutionSession, EngineError> => {
    const fresh = new ExecutionSession({
      sessionId: input.recording.sessionId,
      protocolId: input.recording.protocolId,
      executionPlanId: input.recording.executionPlanId,
      plan: input.plan,
      ...(input.now === undefined ? {} : { now: input.now }),
    });
    const r = replayInto({ session: fresh, recording: input.recording });
    if (!r.ok) {
      return r;
    }
    return Ok(fresh);
  };

  // ========================================================================
  // Read models
  // ========================================================================

  public runtimeState = (): RuntimeState => this.runtime.getState();
  public sessionState = (): SessionState => this.session.state();

  public sessionSnapshot = (): SessionSnapshot => this.session.snapshot();

  public inconsistencies = (): readonly InconsistencyReport[] => this.reports;

  public metrics = (): OrchestratorMetrics =>
    computeOrchestratorMetrics({
      eventsProcessed: this._eventsProcessed,
      eventsSkipped: this._eventsSkipped,
      reports: this.reports,
      replays: this._replays,
    });

  // ========================================================================
  // Subscribe
  // ========================================================================

  public subscribe = (listener: OrchestratorEventListener): OrchestratorUnsubscribe =>
    this.stream.subscribe(listener);

  // ========================================================================
  // Dispose
  // ========================================================================

  public dispose = (): Result<void, EngineError> => {
    if (this._disposed) {
      return Ok(undefined);
    }
    if (this.runtimeUnsubscribe !== null) {
      this.runtimeUnsubscribe();
      this.runtimeUnsubscribe = null;
    }
    if (!isTerminalOrchestratorState(this._state)) {
      this._state = 'disposed';
    }
    this._disposed = true;
    this.emit({
      type: 'orchestrator-disposed',
      monotonicMs: this.clock(),
    });
    this.stream.clear();
    this.recorders = Object.freeze([]);
    return Ok(undefined);
  };

  // ========================================================================
  // Internal: Runtime event handler
  // ========================================================================

  private onRuntimeEvent = (event: RuntimeEvent): void => {
    if (this._disposed || this._state !== 'attached') {
      return;
    }

    // 1. Run consistency checks before translation.
    const planPhases = this.planPhases();
    const totalCycles = this.planCycleCount();
    const newReports = runConsistencyChecks({
      runtimeState: this.runtime.getState(),
      sessionState: this.session.state(),
      event,
      lastSeenMonotonicMs: this.lastSeenMonotonicMs,
      totalCycles,
      validPhases: planPhases,
    });
    if (newReports.length > 0) {
      this.reports = Object.freeze([...this.reports, ...newReports]);
      for (const r of newReports) {
        this.emit({
          type: 'orchestrator-inconsistency',
          monotonicMs: this.clock(),
          report: r,
        });
      }
    }

    // 2. Translate to SessionAction and apply.
    const action = translateRuntimeEvent(event);
    this.applyAction(action, event);

    // 3. Update counters.
    if (action.kind === 'skip') {
      this._eventsSkipped += 1;
    } else {
      this._eventsProcessed += 1;
    }

    // 4. Track last seen monotonic for out-of-order detection.
    if (event.source === 'protocol') {
      this.lastSeenMonotonicMs = event.payload.monotonicMs;
    }
  };

  private applyAction(action: SessionAction, event: RuntimeEvent): void {
    switch (action.kind) {
      case 'skip':
        return;
      case 'start':
        this.session.start();
        break;
      case 'pause':
        this.session.pause();
        break;
      case 'resume':
        this.session.resume();
        break;
      case 'complete':
        this.session.complete();
        break;
      case 'cancel':
        this.session.cancel(action.reason);
        break;
      case 'fail':
        this.session.fail(action.code, action.message);
        break;
      case 'dispose':
        this.session.dispose();
        break;
      case 'recordPhaseChange': {
        if (event.source !== 'protocol') {
          return;
        }
        const p = event.payload;
        if (p.type !== 'protocol-runtime-phase-changed') {
          return;
        }
        const phaseIndex = this.phaseIndexFor(p.currentPhase);
        const phaseDurationMs = this.phaseDurationFor(p.currentPhase);
        this.session.recordPhaseChange({
          phase: p.currentPhase,
          cycleIndex: p.cycleIndex,
          phaseIndex,
          phaseElapsedMs: Math.round(p.phaseProgress * phaseDurationMs),
          phaseDurationMs,
          monotonicMs: p.monotonicMs,
        });
        break;
      }
      case 'recordCycleCompleted': {
        if (event.source !== 'protocol') {
          return;
        }
        const p = event.payload;
        if (p.type !== 'protocol-runtime-cycle-completed') {
          return;
        }
        this.session.recordCycleCompleted({
          cycleIndex: p.cycleIndex,
          cycleElapsedMs: 0,
          totalCycles: this.planCycleCount(),
          monotonicMs: p.monotonicMs,
        });
        break;
      }
      default: {
        const unknown: never = action;
        throw new Error(`Unknown SessionAction: ${String(unknown)}`);
      }
    }

    // Forward emitted Session events to recorders.
    const sessionEvents = this.session.events();
    const lastVersion = this.lastRecordedVersion;
    if (sessionEvents.length > lastVersion) {
      const newEvents = sessionEvents.slice(lastVersion);
      for (const recorder of this.recorders) {
        recorder.recordMany(newEvents);
      }
      this.lastRecordedVersion = sessionEvents.length;
    }
  }

  // ========================================================================
  // Helpers
  // ========================================================================

  private lastRecordedVersion = 0;

  private emit = (event: OrchestratorEvent): void => {
    this.stream.emit(event);
  };

  private planPhases = (): readonly BreathPhase[] => {
    const plan = this.session.plan();
    return plan.phases.map((p) => p.phase);
  };

  private planCycleCount = (): number => this.session.plan().cycles;

  private phaseIndexFor = (phase: BreathPhase): number => {
    const plan = this.session.plan();
    const idx = plan.phases.findIndex((p) => p.phase === phase);
    return idx;
  };

  private phaseDurationFor = (phase: BreathPhase): number => {
    const plan = this.session.plan();
    const p = plan.phases.find((x) => x.phase === phase);
    return p === undefined ? 0 : (p.duration as unknown as number);
  };

  private disposedError = (operation: string): EngineError =>
    new EngineError(`Cannot ${operation} a disposed orchestrator`, {
      code: 'orchestrator_disposed',
      severity: 'error',
      context: { operation },
    });
}

// Silence unused-import warning (Failure is re-exported for tests).
export type { Failure };
