/**
 * AnimationEngine — produces immutable AnimationFrames from Runtime,
 * Breath, Timer, and Session events. No rendering, no UI.
 *
 * Lifecycle:
 *
 *   const engine = new AnimationEngine({ runtime, breath, ... });
 *   engine.start();           // subscribe to engines + emit idle frame
 *   engine.update(now);       // refresh frame (call per RAF tick)
 *   engine.currentFrame();    // read latest frame
 *   engine.subscribe(listener); // observe frames + lifecycle events
 *   engine.pause();           // freeze frame
 *   engine.resume();
 *   engine.dispose();         // terminal, no further emissions
 *
 * Sprint 8 deliverable: deterministic, drift-free, allocation-light.
 * Sprint 9+ uses this engine to build the visual experience.
 */

import type { BreathEngine, BreathPhase, CurveName } from '@core/breath-engine';
import type { ExecutionSession } from '@core/execution-session';
import type { RuntimeEngine, RuntimeEvent, RuntimeUnsubscribe } from '@core/runtime';
import type { TimerEngine, TimerEvent, Unsubscribe as TimerUnsubscribe } from '@core/timer-engine';

import type { AnimationEngineDeps } from './AnimationEngineDeps';
import { createAnimationEventStream } from './AnimationEventStream';
import type { AnimationConfig } from '../domain/AnimationConfig';
import {
  DEFAULT_ANIMATION_CONFIG,
  clamp,
  validateAnimationConfig,
} from '../domain/AnimationConfig';
import type { AnimationEngineState } from '../domain/AnimationEngineState';
import {
  canAnimationEngineTransition,
  isAnimationEngineState,
  isTerminalAnimationEngineState,
} from '../domain/AnimationEngineState';
import type { AnimationEvent } from '../domain/AnimationEvent';
import type { AnimationFrame } from '../domain/AnimationFrame';
import type { AnimationMetrics } from '../domain/AnimationMetrics';
import { EMPTY_ANIMATION_METRICS } from '../domain/AnimationMetrics';
import type { AnimationPhase } from '../domain/AnimationPhase';
import { computeAnimationFrame, buildIdleFrame } from '../util/frame-computation';
import type { HoldPosition } from '../util/phase-mapping';
import { mapBreathPhase } from '../util/phase-mapping';

export const ANIMATION_ENGINE_ID = 'animation-engine-v1' as const;

/** Internal phase change state. */
interface PhaseState {
  readonly phase: AnimationPhase;
  readonly phaseStartedAtMs: number;
  readonly phaseDurationMs: number;
  readonly hold: HoldPosition;
}

const computeProgress = (state: PhaseState, nowMs: number): number => {
  if (state.phaseDurationMs <= 0) {
    return 1;
  }
  const elapsed = nowMs - state.phaseStartedAtMs;
  return clamp(elapsed / state.phaseDurationMs, 0, 1);
};

export class AnimationEngine {
  private readonly _config: AnimationConfig;
  private readonly _runtime: RuntimeEngine;
  private readonly _breath: BreathEngine | undefined;
  private readonly _timer: TimerEngine | undefined;
  private readonly _session: ExecutionSession | undefined;
  private readonly _now: () => number;
  private readonly _onListenerError?: (err: unknown, context: { readonly phase: string }) => void;

  private readonly _stream = createAnimationEventStream();

  private _state: AnimationEngineState = 'idle';
  private _frame: AnimationFrame;
  private _phase: PhaseState = {
    phase: 'idle',
    phaseStartedAtMs: 0,
    phaseDurationMs: 0,
    hold: 'none',
  };
  private _metrics: AnimationMetrics = EMPTY_ANIMATION_METRICS;

  private _runtimeUnsub: RuntimeUnsubscribe | null = null;
  private _breathUnsub: (() => void) | null = null;
  private _timerUnsub: TimerUnsubscribe | null = null;

  constructor(deps: AnimationEngineDeps) {
    this._config = deps.config ?? DEFAULT_ANIMATION_CONFIG;
    validateAnimationConfig(this._config);
    this._runtime = deps.runtime;
    this._breath = deps.breath;
    this._timer = deps.timer;
    this._session = deps.session;
    this._now = deps.now ?? ((): number => Date.now());
    this._onListenerError = deps.onListenerError ?? (() => undefined);

    this._frame = buildIdleFrame(this._config, this._now());
  }

  /** Stable identifier. */
  public id = (): string => ANIMATION_ENGINE_ID;

  /** Engine state. */
  public state = (): AnimationEngineState => this._state;

  /** The current frame. Always defined; returns idle if not started. */
  public currentFrame = (): AnimationFrame => this._frame;

  /** Derived metrics. */
  public metrics = (): AnimationMetrics => this._metrics;

  /** Current visual phase. */
  public phase = (): AnimationPhase => this._phase.phase;

  /** Current curve (read from config). */
  public easingCurve = (): CurveName => this._config.easingCurve;

  /** Subscribe to engine events. */
  public subscribe = (listener: (event: AnimationEvent) => void): (() => void) => {
    return this._stream.subscribe(listener);
  };

  /** Start the engine: subscribe to upstream engines + emit idle frame. */
  public start = (): void => {
    if (!canAnimationEngineTransition(this._state, 'running')) {
      return;
    }
    this._state = 'running';
    this._metrics = {
      ...this._metrics,
      attachedSince: this._now(),
    };
    this._wireUpstream();
    this._emitLifecycle('animation-engine-started');
    // Initial frame
    this.update(this._now());
  };

  /** Refresh the frame based on current time. Safe to call at any cadence. */
  public update = (nowMs?: number): AnimationFrame => {
    if (this._state === 'disposed') {
      return this._frame;
    }
    const t = nowMs ?? this._now();
    const progress = computeProgress(this._phase, t);
    const remainingMs =
      this._phase.phaseDurationMs === 0
        ? 0
        : Math.max(0, this._phase.phaseDurationMs - (t - this._phase.phaseStartedAtMs));

    const next = computeAnimationFrame({
      phase: this._phase.phase,
      normalizedProgress: progress,
      hold: this._phase.hold,
      config: this._config,
      timestamp: t,
      remainingTime: remainingMs,
    });
    this._frame = next;
    this._metrics = {
      ...this._metrics,
      updates: this._metrics.updates + 1,
      lastFrameTimestamp: t,
    };
    if (this._state === 'running') {
      this._emitFrame(next);
    }
    return next;
  };

  /** Pause: freeze the frame and emit a paused event. */
  public pause = (): void => {
    if (!canAnimationEngineTransition(this._state, 'paused')) {
      return;
    }
    const frozen = this._frame;
    this._state = 'paused';
    this._emitLifecycleWithFrame('animation-engine-paused', frozen);
  };

  /** Resume: continue emitting frames. */
  public resume = (): void => {
    if (!canAnimationEngineTransition(this._state, 'running')) {
      return;
    }
    this._state = 'running';
    this._emitLifecycle('animation-engine-resumed');
    // Reset the phase start so progress restarts cleanly.
    this._phase = { ...this._phase, phaseStartedAtMs: this._now() };
    this.update(this._now());
  };

  /** Dispose: terminal. No further emissions. */
  public dispose = (): void => {
    if (isTerminalAnimationEngineState(this._state)) {
      return;
    }
    this._state = 'disposed';
    this._emitLifecycle('animation-engine-disposed');
    this._runtimeUnsub?.();
    this._runtimeUnsub = null;
    this._breathUnsub?.();
    this._breathUnsub = null;
    this._timerUnsub?.();
    this._timerUnsub = null;
    this._stream.clear();
  };

  // REDACTED
  // Internals
  // REDACTED

  private _wireUpstream(): void {
    if (this._runtimeUnsub === null) {
      this._runtimeUnsub = this._runtime.subscribe((event: RuntimeEvent) => {
        try {
          this._onRuntimeEvent(event);
        } catch (err) {
          this._reportError(err, 'runtime-event');
        }
      });
    }
    if (this._breath && this._breathUnsub === null) {
      this._breathUnsub = this._breath.subscribe((event) => {
        try {
          this._onBreathEvent(event);
        } catch (err) {
          this._reportError(err, 'breath-event');
        }
      });
    }
    if (this._timer && this._timerUnsub === null) {
      this._timerUnsub = this._timer.subscribe((event: TimerEvent) => {
        try {
          this._onTimerEvent(event);
        } catch (err) {
          this._reportError(err, 'timer-event');
        }
      });
    }
  }

  private _onRuntimeEvent(event: RuntimeEvent): void {
    const payload = event.payload;
    switch (payload.type) {
      case 'protocol-runtime-started':
        this._transition('preparing', 0, 0, 'none');
        return;
      case 'protocol-runtime-paused':
        if (this._state === 'running') {
          this.pause();
        }
        return;
      case 'protocol-runtime-resumed':
        if (this._state === 'paused') {
          this.resume();
        }
        return;
      case 'protocol-runtime-stopped': {
        const reason = (payload as { reason?: string }).reason ?? 'cancelled';
        this._handleStop(reason);
        return;
      }
      case 'protocol-runtime-completed':
        this._transition('completed', 0, 0, 'none');
        return;
      case 'protocol-runtime-phase-changed': {
        // The Runtime payload carries `currentPhase` (BreathPhase) and
        // `phaseProgress` (0..1). We don't have the absolute duration
        // here, so we derive it from the session plan when injected,
        // otherwise default to a reasonable inhale/exhale duration.
        const currentPhase = (payload as { currentPhase?: BreathPhase }).currentPhase;
        const durationMs = this._phaseDurationFor(currentPhase ?? 'inhaling');
        this._onPhaseChanged(currentPhase ?? 'inhaling', durationMs);
        return;
      }
      default:
        return;
    }
  }

  private _onBreathEvent(event: {
    type: string;
    phase?: BreathPhase;
    phaseDurationMs?: number;
  }): void {
    if (event.type === 'breath-phase-changed' && event.phase !== undefined) {
      this._onPhaseChanged(event.phase, event.phaseDurationMs ?? 0);
    }
  }

  private _onTimerEvent(_event: TimerEvent): void {
    // Timer ticks trigger a frame refresh only when the engine is
    // running. This keeps animation in lock-step with the master
    // clock without depending on RAF.
    if (this._state === 'running') {
      this.update(this._now());
    }
  }

  private _onPhaseChanged(breathPhase: BreathPhase, phaseDurationMs: number): void {
    const { animation, hold } = mapBreathPhase(breathPhase);
    const safeDuration = phaseDurationMs > 0 ? phaseDurationMs : 1;
    this._transition(animation, this._now(), safeDuration, hold);
  }

  /**
   * Derive phase duration from the session plan when available;
   * otherwise fall back to a sane default. Used when Runtime
   * events don't carry the absolute duration.
   */
  private _phaseDurationFor(breathPhase: BreathPhase): number {
    const DEFAULT_DURATION_MS = 4000;
    if (!this._session) {
      return DEFAULT_DURATION_MS;
    }
    const plan = this._session.plan();
    if (!plan || !plan.phases || plan.phases.length === 0) {
      return DEFAULT_DURATION_MS;
    }
    // The plan stores per-phase durations keyed by phase name.
    const match = plan.phases.find((p) => p.phase === breathPhase);
    if (!match) {
      return DEFAULT_DURATION_MS;
    }
    return match.duration > 0 ? match.duration : DEFAULT_DURATION_MS;
  }

  private _transition(
    phase: AnimationPhase,
    startedAtMs: number,
    durationMs: number,
    hold: HoldPosition,
  ): void {
    if (this._state === 'disposed') {
      return;
    }
    this._phase = {
      phase,
      phaseStartedAtMs: startedAtMs || this._now(),
      phaseDurationMs: Math.max(0, durationMs),
      hold,
    };
    this._metrics = {
      ...this._metrics,
      phaseChanges: this._metrics.phaseChanges + 1,
    };
    this.update(this._now());
  }

  private _handleStop(_reason: string): void {
    // Returning to idle on stop/cancel. We don't transition to 'completed'
    // because cancellation ≠ completion.
    this._transition('idle', this._now(), 0, 'none');
  }

  private _emitFrame(frame: AnimationFrame): void {
    this._metrics = {
      ...this._metrics,
      framesEmitted: this._metrics.framesEmitted + 1,
    };
    this._stream.emit(
      {
        type: 'animation-frame',
        monotonicMs: frame.timestamp,
        frame,
      },
      (err) => this._reportError(err, 'frame-emit'),
    );
  }

  private _emitLifecycle(
    type: 'animation-engine-started' | 'animation-engine-resumed' | 'animation-engine-disposed',
  ): void {
    this._stream.emit({ type, monotonicMs: this._now() }, (err) => this._reportError(err, type));
  }

  private _emitLifecycleWithFrame(type: 'animation-engine-paused', frame: AnimationFrame): void {
    this._stream.emit({ type, monotonicMs: this._now(), frozenFrame: frame }, (err) =>
      this._reportError(err, type),
    );
  }

  private _reportError(err: unknown, phase: string): void {
    if (this._onListenerError) {
      try {
        this._onListenerError(err, { phase });
      } catch {
        // swallow
      }
    }
  }

  /**
   * Read-only convenience accessor used by some tests: returns the
   * current session plan if a session was injected, else null.
   */
  public sessionPlan = (): ReadonlyArray<{
    readonly phase: BreathPhase;
    readonly duration: number;
  }> | null => {
    if (!this._session) {
      return null;
    }
    const plan = this._session.plan();
    if (!plan) {
      return null;
    }
    return plan.phases.map((p) => ({ phase: p.phase, duration: p.duration }));
  };
}

/** Re-export for barrel. */
export { isAnimationEngineState };
