/**
 * RuntimeEngine — the Facade and Orchestrator for the AraFlow Core.
 *
 * Single public API for the entire Core. Wraps TimerEngine, BreathEngine,
 * and ProtocolRuntime behind a 12-method API and a unified event stream.
 *
 * Lifecycle FSM (RuntimeState):
 *
 *   uninitialized ─loadProtocol→ loaded ─start→ starting → running ⇄ paused
 *                                                            → stopping → stopped | completed | errored
 *   any ─dispose→ disposed (terminal)
 *
 * Gaps closed vs raw ProtocolRuntime (see ADR-023 and 40_SPRINT4_REPORT.md):
 *   - 'errored' state is actually reachable (Runtime listens for
 *     protocol-runtime-errored + detects other failure signals)
 *   - Pause-outlasts-plan is detected and rejected at resume()
 *   - Compile-time warnings are surfaced as Runtime events
 *   - 3 engines emit events through 1 stream with source discriminant
 *   - Snapshot merges all 3 engine snapshots into a single shape
 *
 * Constraints (frozen engines — no internals touched):
 *   - Timer Engine v1.0.0 — used as-is via TimerLike adapter
 *   - Breath Engine v1.0.0 — created lazily inside loadProtocol
 *   - Protocol Compiler v1.0.0 — used via compile() convenience method
 *   - ProtocolRuntime v1.0.0 — used as the orchestrator engine
 *   - Shared Contracts v2.5.0 — canonical types (EngineId, Result, AppError, Failure, …)
 */

import {
  EngineError,
  EngineId,
  Err,
  type Failure,
  Ok,
  type Result,
} from '@araflow/shared-contracts';

import {
  createBreathEngine,
  type BreathCycleConfig,
  type BreathEngine,
  type BreathEvent,
} from '@core/breath-engine';
import {
  ProtocolCompiler,
  ProtocolRuntime,
  type ProtocolExecutionPlan,
  type ProtocolRuntimeEvent,
  type ProtocolSource,
} from '@core/protocol-compiler';
import { createTimerEngine, type TimerEngine, type TimerEvent } from '@core/timer-engine';

import type { RuntimeEngineDeps } from './RuntimeEngineDeps';
import { createRuntimeEventStream, type RuntimeEventStream } from './RuntimeEventStream';
import type { RuntimeEventListener, RuntimeUnsubscribe } from '../domain/RuntimeEvent';
import type { RuntimeLifecycleEvent } from '../domain/RuntimeLifecycleEvent';
import type { EventCounters, RuntimeMetrics } from '../domain/RuntimeMetrics';
import type { RuntimeSnapshot } from '../domain/RuntimeSnapshot';
import type { RuntimeState } from '../domain/RuntimeState';
import { isTerminalRuntimeState } from '../domain/RuntimeState';
import {
  aggregateMetrics,
  EMPTY_EVENT_COUNTERS,
  type AggregateMetricsInput,
} from '../util/aggregate-metrics';
import { planToBreathConfig } from '../util/plan-to-breath-config';
import { createTimerLikeAdapter } from '../util/timer-like-adapter';

interface EngineSubscriptions {
  timer: RuntimeUnsubscribe | null;
  breath: RuntimeUnsubscribe | null;
  protocol: RuntimeUnsubscribe | null;
}

export class RuntimeEngine {
  // --- Identity & state ---
  private readonly id: EngineId;
  private _state: RuntimeState = 'uninitialized';

  // --- Owned engines ---
  private readonly timerEngine: TimerEngine;
  private readonly timerLike: ReturnType<typeof createTimerLikeAdapter>;
  private breathEngine: BreathEngine | null = null;
  private readonly protocolRuntime: ProtocolRuntime;
  private readonly compiler: ProtocolCompiler;

  // --- Event plumbing ---
  private readonly stream: RuntimeEventStream;
  private readonly subs: EngineSubscriptions = {
    timer: null,
    breath: null,
    protocol: null,
  };

  // --- Plan / warnings ---
  private _plan: ProtocolExecutionPlan | null = null;
  private _warnings: readonly Failure[] = [];

  // --- Counters (idempotent — derived not counted in aggregate) ---
  private _counters: EventCounters = { ...EMPTY_EVENT_COUNTERS };
  private _tickCount = 0;
  private _pauseCount = 0;
  private _totalPausedMs = 0;
  private _errors = 0;

  constructor(deps: RuntimeEngineDeps) {
    this.id = deps.runtimeId;
    this.stream = createRuntimeEventStream(deps.onListenerError);

    // Timer Engine — own it.
    this.timerEngine = deps.timerEngine ?? createTimerEngine();
    this.timerLike = createTimerLikeAdapter(this.timerEngine);

    // Protocol Runtime — own it. Timer is the seam.
    this.protocolRuntime = new ProtocolRuntime({
      runtimeId: EngineId(`${deps.runtimeId}-protocol`),
      timer: this.timerLike,
      ...(deps.onListenerError !== undefined
        ? {
            onListenerError: (err, listener) =>
              deps.onListenerError?.(err, listener as RuntimeEventListener),
          }
        : {}),
    });

    // Compiler — for the compile() convenience method.
    this.compiler = new ProtocolCompiler({ compiledBy: EngineId(`${deps.runtimeId}-compiler`) });

    // Bridge engine events into the unified stream.
    this.subs.timer = this.timerEngine.subscribe((event: TimerEvent) => {
      this._counters = { ...this._counters, timer: this._counters.timer + 1 };
      this.stream.emit({ source: 'timer', payload: event });
    });
    this.subs.protocol = this.protocolRuntime.subscribe((event: ProtocolRuntimeEvent) => {
      this._counters = { ...this._counters, protocol: this._counters.protocol + 1 };
      this.onProtocolEvent(event);
      this.stream.emit({ source: 'protocol', payload: event });
    });
  }

  // ============================================================
  // Public API — Lifecycle
  // ============================================================

  /**
   * Load a pre-compiled execution plan. Transitions to `'loaded'`.
   * Creates and subscribes the Breath Engine on demand.
   */
  public loadProtocol = (plan: ProtocolExecutionPlan): Result<void, EngineError> => {
    if (isTerminalRuntimeState(this._state)) {
      return Err(
        new EngineError(`Cannot loadProtocol in terminal state '${this._state}'`, {
          code: 'runtime_invalid_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }
    if (this._state !== 'uninitialized' && this._state !== 'loaded') {
      return Err(
        new EngineError(`Cannot loadProtocol in state '${this._state}'`, {
          code: 'runtime_invalid_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }

    const loadResult = this.protocolRuntime.load(plan);
    if (!loadResult.ok) {
      return loadResult;
    }

    this._plan = plan;
    this._state = 'loaded';

    // Lazily create Breath Engine for this plan.
    if (plan.cycles > 0) {
      const breathConfig: BreathCycleConfig = planToBreathConfig(plan);
      if (this.breathEngine === null) {
        this.breathEngine = createBreathEngine({
          monotonic: { now: () => this.timerEngine.getTotalElapsedMs() },
          timerEngine: this.timerEngine,
          config: breathConfig,
        });
        this.subs.breath = this.breathEngine.subscribe((event: BreathEvent) => {
          this._counters = { ...this._counters, breath: this._counters.breath + 1 };
          this.stream.emit({ source: 'breath', payload: event });
        });
      }
    }

    return Ok(undefined);
  };

  /**
   * Convenience: compile a ProtocolSource and load the resulting plan.
   * On success: emits runtime-warnings (if any) and transitions to 'loaded'.
   * On failure: emits runtime-compile-failed and returns Err.
   */
  public compile = (source: ProtocolSource): Result<void, EngineError> => {
    const result = this.compiler.compile(source);
    if (result.plan === null) {
      this._state = 'errored';
      const failures = result.failures;
      const warnings = result.warnings;
      this._errors += 1;
      const ev: RuntimeLifecycleEvent = {
        type: 'runtime-compile-failed',
        failures,
        warnings,
        monotonicMs: this.timerEngine.getTotalElapsedMs(),
      };
      this._counters = { ...this._counters, runtime: this._counters.runtime + 1 };
      this.stream.emit({ source: 'runtime', payload: ev });
      return Err(
        new EngineError('Protocol compilation failed', {
          code: 'runtime_compile_failed',
          severity: 'error',
          context: { failureCount: failures.length },
        }),
      );
    }

    this._warnings = result.warnings;
    if (result.warnings.length > 0) {
      const ev: RuntimeLifecycleEvent = {
        type: 'runtime-warnings',
        warnings: result.warnings,
        monotonicMs: this.timerEngine.getTotalElapsedMs(),
      };
      this._counters = { ...this._counters, runtime: this._counters.runtime + 1 };
      this.stream.emit({ source: 'runtime', payload: ev });
    }

    return this.loadProtocol(result.plan);
  };

  /**
   * Begin execution. Transitions: loaded → starting → running.
   * Breath Engine is started after Timer Engine (it requires it).
   */
  public start = (): Result<void, EngineError> => {
    if (isTerminalRuntimeState(this._state)) {
      return Err(
        new EngineError(`Cannot start in terminal state '${this._state}'`, {
          code: 'runtime_invalid_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }
    if (this._state !== 'loaded' && this._state !== 'stopped' && this._state !== 'completed') {
      return Err(
        new EngineError(`Cannot start in state '${this._state}'`, {
          code: 'runtime_invalid_state',
          severity: 'error',
          context: { state: this._state },
        }),
      );
    }

    this._state = 'starting';
    this.timerEngine.start();
    if (this.breathEngine !== null) {
      this.breathEngine.start();
    }
    const result = this.protocolRuntime.start();
    if (!result.ok) {
      this._state = 'errored';
      return result;
    }
    this._state = 'running';
    return Ok(undefined);
  };

  /**
   * Pause execution. No-op if not running.
   */
  public pause = (): Result<void, EngineError> => {
    if (this._state !== 'running') {
      return Ok(undefined);
    }
    const result = this.protocolRuntime.pause();
    if (!result.ok) {
      return result;
    }
    this._state = 'paused';
    return Ok(undefined);
  };

  /**
   * Resume from pause. Detects pause-outlasts-plan (gap fix from Sprint 3)
   * and rejects the resume if elapsed would go negative.
   */
  public resume = (): Result<void, EngineError> => {
    if (this._state !== 'paused') {
      return Ok(undefined);
    }
    // Pause-outlasts-plan guard — fix for Sprint 3 gap.
    if (this._plan !== null) {
      const planned = this._plan.totalDuration as unknown as number;
      const elapsed = this.timerEngine.getTotalElapsedMs() - this._totalPausedMs;
      if (elapsed >= planned) {
        return Err(
          new EngineError('Pause duration outlasts plan — refusing to resume', {
            code: 'runtime_pause_outlasts_plan',
            severity: 'error',
            context: { elapsedMs: elapsed, plannedDurationMs: planned },
          }),
        );
      }
    }
    const result = this.protocolRuntime.resume();
    if (!result.ok) {
      return result;
    }
    this._state = 'running';
    return Ok(undefined);
  };

  /**
   * Cancel execution. Transitions to 'stopping' then 'stopped'.
   * Stops all 3 engines.
   */
  public cancel = (): Result<void, EngineError> => {
    if (isTerminalRuntimeState(this._state)) {
      return Ok(undefined);
    }
    this._state = 'stopping';
    const result = this.protocolRuntime.stop();
    if (this.breathEngine !== null) {
      this.breathEngine.cancel();
    }
    if (this.timerEngine.getState() === 'running') {
      this.timerEngine.stop();
    }
    if (!result.ok) {
      this._state = 'errored';
      return result;
    }
    this._state = 'stopped';
    return Ok(undefined);
  };

  /**
   * Release all resources. Terminal. Subsequent calls are no-ops.
   * Emits runtime-disposed before clearing listeners.
   */
  public dispose = (): void => {
    if (this._state === 'disposed') {
      return;
    }
    if (this._state !== 'stopped' && this._state !== 'completed' && this._state !== 'errored') {
      this.cancel();
    }
    if (this.breathEngine !== null) {
      this.breathEngine.dispose();
    }
    if (this.subs.timer !== null) {
      this.subs.timer();
    }
    if (this.subs.breath !== null) {
      this.subs.breath();
    }
    if (this.subs.protocol !== null) {
      this.subs.protocol();
    }
    this.subs.timer = null;
    this.subs.breath = null;
    this.subs.protocol = null;

    const ev: RuntimeLifecycleEvent = {
      type: 'runtime-disposed',
      monotonicMs: this.timerEngine.getTotalElapsedMs(),
    };
    this.stream.emit({ source: 'runtime', payload: ev });
    this.stream.clear();
    this._state = 'disposed';
  };

  /**
   * Forward AppState background/foreground notifications to all 3 engines.
   * App layer (mobile) is responsible for calling these.
   */
  public notifyBackground = (): void => {
    this.timerEngine.notifyBackground();
  };

  public notifyForeground = (): void => {
    this.timerEngine.notifyForeground();
  };

  // ============================================================
  // Public API — Observation
  // ============================================================

  public subscribe = (listener: RuntimeEventListener): RuntimeUnsubscribe =>
    this.stream.subscribe(listener);

  public getState = (): RuntimeState => this._state;

  public getExecutionPlan = (): ProtocolExecutionPlan | null => this._plan;

  public getWarnings = (): readonly Failure[] => this._warnings;

  public getMetrics = (): RuntimeMetrics => {
    const input: AggregateMetricsInput = {
      snapshot: this.snapshot(),
      plan: this._plan,
      counters: this._counters,
      pauseCount: this._pauseCount,
      totalPausedMs: this._totalPausedMs,
      tickCount: this._tickCount,
      warnings: this._warnings.length,
      errors: this._errors,
    };
    return aggregateMetrics(input);
  };

  public snapshot = (): RuntimeSnapshot => ({
    runtimeId: this.id,
    state: this._state,
    plan: this._plan,
    protocol:
      this._state === 'uninitialized' || this._state === 'disposed'
        ? null
        : this.protocolRuntime.snapshot(),
    breath: this.breathEngine === null ? null : this.breathEngine.snapshot(),
    timer: this._state === 'disposed' ? null : this.timerEngine.snapshot(),
  });

  // ============================================================
  // Internal
  // ============================================================

  private onProtocolEvent = (event: ProtocolRuntimeEvent): void => {
    switch (event.type) {
      case 'protocol-runtime-tick':
        this._tickCount += 1;
        break;
      case 'protocol-runtime-paused':
        this._pauseCount += 1;
        break;
      case 'protocol-runtime-resumed':
        this._totalPausedMs += event.pausedForMs;
        break;
      case 'protocol-runtime-completed':
        if (this._state === 'running' || this._state === 'paused') {
          this._state = 'completed';
        }
        // Tear down timer + breath (they outlive ProtocolRuntime).
        if (this.breathEngine !== null) {
          this.breathEngine.cancel();
        }
        if (this.timerEngine.getState() === 'running') {
          this.timerEngine.stop();
        }
        {
          const completedEv: RuntimeLifecycleEvent = {
            type: 'runtime-completed',
            totalElapsedMs: event.totalElapsedMs,
            monotonicMs: event.monotonicMs,
          };
          this._counters = { ...this._counters, runtime: this._counters.runtime + 1 };
          this.stream.emit({ source: 'runtime', payload: completedEv });
        }
        break;
      case 'protocol-runtime-errored':
        this._state = 'errored';
        this._errors += 1;
        {
          const errorEv: RuntimeLifecycleEvent = {
            type: 'runtime-error',
            code: event.code,
            message: event.message,
            monotonicMs: event.monotonicMs,
          };
          this._counters = { ...this._counters, runtime: this._counters.runtime + 1 };
          this.stream.emit({ source: 'runtime', payload: errorEv });
        }
        break;
      case 'protocol-runtime-stopped':
        if (
          event.reason === 'errored' &&
          this._state !== 'stopped' &&
          this._state !== 'completed'
        ) {
          this._state = 'errored';
        }
        break;
      default:
        break;
    }
  };
}
