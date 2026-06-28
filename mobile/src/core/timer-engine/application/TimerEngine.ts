/**
 * TimerEngine — orquestrador principal. Implementa a máquina de
 * estados e o tick scheduler com drift correction.
 *
 * Princípios:
 *   - Determinístico: dado mesmo ClockProvider e MonotonicClock,
 *     comportamento é reproduzível.
 *   - Re-entrante: chamada de pause/resume/stop dentro de listener
 *     é tratada corretamente.
 *   - Thread-safe: JS é single-threaded, mas operações são atômicas
 *     (nenhuma alteração parcial de estado visível externamente).
 *   - Sem dependência de UI, React, RN, ou plataforma específica.
 *
 * Estado interno:
 *   - state: 'idle' | 'running' | 'paused' | 'stopped'
 *   - mode: 'high-precision' | 'balanced' | 'low-power'
 *   - timeScale: number (default 1.0)
 *   - tickIntervalMs: number (derived from mode)
 *   - sessionStartedAtMs: number | null
 *   - pausedAtMs: number | null
 *   - backgroundedAtMs: number | null
 *   - tickIndex: number
 *   - totalActiveMs: number (cumulative, exclude paused time)
 *   - totalPausedMs: number
 *   - totalBackgroundedMs: number
 *   - activeHandle: ClockHandle | null
 *
 * Invariantes:
 *   - activeHandle !== null  <=>  state === 'running'
 *   - totalActiveMs é a soma dos intervalos ativos (running).
 *   - totalElapsedMs (exposto) inclui apenas tempo em running.
 */

import { AppError } from '@shared/errors';

import {
  DEFAULT_TIMER_MODE,
  DEFAULT_TIME_SCALE,
  isValidTimeScale,
  MAX_TIME_SCALE,
  MIN_TIME_SCALE,
  TIMER_MODE_TICK_INTERVAL_MS,
} from '../domain';
import type {
  ClockHandle,
  ClockProvider,
  DriftMeasurement,
  MonotonicClock,
  TimerEvent,
  TimerListener,
  TimerMode,
  TimerState,
  Unsubscribe,
  WallClock,
} from '../domain';
import { createEventDispatcher, type EventDispatcher } from './EventEmitter';
import { createDriftCorrector, type DriftCorrectionStrategy } from './DriftCorrector';

export interface TimerEngineDeps {
  readonly monotonic: MonotonicClock;
  readonly wall: WallClock;
  readonly clockProvider: ClockProvider;
  readonly mode?: TimerMode;
  readonly timeScale?: number;
  readonly onListenerError?: (error: unknown, listener: TimerListener) => void;
}

export interface TimerEngineSnapshot {
  readonly state: TimerState;
  readonly mode: TimerMode;
  readonly timeScale: number;
  readonly tickIntervalMs: number;
  readonly totalElapsedMs: number;
  readonly totalActiveMs: number;
  readonly totalPausedMs: number;
  readonly totalBackgroundedMs: number;
  readonly tickIndex: number;
  readonly listenerCount: number;
}

export class TimerEngine {
  private readonly monotonic: MonotonicClock;
  private readonly wall: WallClock;
  private readonly clockProvider: ClockProvider;
  private readonly events: EventDispatcher;
  private readonly drift: DriftCorrectionStrategy;

  private _state: TimerState = 'idle';
  private _mode: TimerMode;
  private _timeScale: number;
  private _tickIntervalMs: number;

  private sessionStartedAtMonotonicMs: number | null = null;
  private sessionStartedAtWallIso: string | null = null;
  private pausedAtMonotonicMs: number | null = null;
  private backgroundedAtMonotonicMs: number | null = null;
  private lastTickMonotonicMs: number | null = null;
  private activeHandle: ClockHandle | null = null;

  private _tickIndex = 0;
  private _totalActiveMs = 0;
  private _totalPausedMs = 0;
  private _totalBackgroundedMs = 0;
  private lastDriftMs = 0;
  private lastDriftEmitted = false;

  public constructor(deps: TimerEngineDeps) {
    if (deps.monotonic === undefined || deps.wall === undefined || deps.clockProvider === undefined) {
      throw new AppError('TimerEngine requires monotonic, wall, and clockProvider', {
        code: 'timer_missing_dependencies',
        severity: 'fatal',
      });
    }
    this.monotonic = deps.monotonic;
    this.wall = deps.wall;
    this.clockProvider = deps.clockProvider;
    this._mode = deps.mode ?? DEFAULT_TIMER_MODE;
    const initialScale = deps.timeScale ?? DEFAULT_TIME_SCALE;
    this._timeScale = isValidTimeScale(initialScale) ? initialScale : DEFAULT_TIME_SCALE;
    this._tickIntervalMs = TIMER_MODE_TICK_INTERVAL_MS[this._mode];
    this.events = createEventDispatcher(deps.onListenerError);
    this.drift = createDriftCorrector(this.monotonic);
  }

  // REDACTED
  // Public API — Lifecycle
  // REDACTED

  /**
   * Starts the timer. Idempotent in `idle` state; no-op if already
   * running. Throws AppError if state is `stopped` (must reset first).
   */
  public start(): void {
    if (this._state === 'running') {
      return;
    }
    if (this._state === 'paused') {
      throw new AppError('Cannot start from paused; use resume() instead', {
        code: 'timer_invalid_state',
        severity: 'warn',
        context: { state: this._state },
      });
    }
    if (this._state === 'stopped') {
      throw new AppError('Cannot start from stopped; use reset() first', {
        code: 'timer_invalid_state',
        severity: 'warn',
        context: { state: this._state },
      });
    }

    const monotonicMs = this.monotonic.now();
    const wallIso = this.wall.isoNow();
    this.sessionStartedAtMonotonicMs = monotonicMs;
    this.sessionStartedAtWallIso = wallIso;
    this.lastTickMonotonicMs = monotonicMs;
    this._state = 'running';

    this.emit({
      type: 'started',
      monotonicMs,
      wallIso,
      startMonotonicMs: monotonicMs,
      startWallIso: wallIso,
    });

    this.scheduleNextTick();
  }

  /**
   * Pauses the timer. Only valid in `running` state. No-op otherwise.
   */
  public pause(): void {
    if (this._state !== 'running') {
      return;
    }
    const monotonicMs = this.monotonic.now();
    if (this.lastTickMonotonicMs !== null) {
      this._totalActiveMs += this.scaledDelta(this.lastTickMonotonicMs, monotonicMs);
    }
    this.cancelActiveHandle();
    this.pausedAtMonotonicMs = monotonicMs;
    this._state = 'paused';

    this.emit({
      type: 'paused',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      totalElapsedMs: this._totalActiveMs,
      pausedAtMonotonicMs: monotonicMs,
    });
  }

  /**
   * Resumes from paused. Only valid in `paused` state. No-op otherwise.
   */
  public resume(): void {
    if (this._state !== 'paused') {
      return;
    }
    const monotonicMs = this.monotonic.now();
    const pausedForMs =
      this.pausedAtMonotonicMs !== null
        ? this.scaledDelta(this.pausedAtMonotonicMs, monotonicMs)
        : 0;
    this._totalPausedMs += pausedForMs;
    this.pausedAtMonotonicMs = null;
    this.lastTickMonotonicMs = monotonicMs;
    this._state = 'running';

    this.emit({
      type: 'resumed',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      totalElapsedMs: this._totalActiveMs,
      pausedForMs,
    });

    this.scheduleNextTick();
  }

  /**
   * Stops the timer. Terminal state. Can only be reset() after.
   */
  public stop(): void {
    if (this._state === 'idle' || this._state === 'stopped') {
      return;
    }
    const monotonicMs = this.monotonic.now();
    if (this._state === 'running' && this.lastTickMonotonicMs !== null) {
      this._totalActiveMs += this.scaledDelta(this.lastTickMonotonicMs, monotonicMs);
    }
    this.cancelActiveHandle();
    this._state = 'stopped';

    this.emit({
      type: 'stopped',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      totalElapsedMs: this._totalActiveMs,
      totalActiveMs: this._totalActiveMs,
    });
  }

  /**
   * Resets the timer to idle. Wipes all session state.
   */
  public reset(): void {
    const previousState = this._state;
    this.cancelActiveHandle();
    this._state = 'idle';
    this.sessionStartedAtMonotonicMs = null;
    this.sessionStartedAtWallIso = null;
    this.pausedAtMonotonicMs = null;
    this.backgroundedAtMonotonicMs = null;
    this.lastTickMonotonicMs = null;
    this._tickIndex = 0;
    this._totalActiveMs = 0;
    this._totalPausedMs = 0;
    this._totalBackgroundedMs = 0;
    this.lastDriftMs = 0;
    this.lastDriftEmitted = false;

    this.emit({
      type: 'reset',
      monotonicMs: this.monotonic.now(),
      wallIso: this.wall.isoNow(),
      previousState,
    });
  }

  // REDACTED
  // Public API — App lifecycle
  // REDACTED

  /**
   * Called by the app layer when the app enters background.
   * Auto-pauses if currently running so the JS thread suspension
   * does not cause erroneous elapsed time accumulation.
   */
  public notifyBackground(): void {
    if (this._state !== 'running') {
      return;
    }
    const monotonicMs = this.monotonic.now();
    this.backgroundedAtMonotonicMs = monotonicMs;
    this.cancelActiveHandle();
    this._state = 'paused';

    this.emit({
      type: 'backgrounded',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      totalElapsedMs: this._totalActiveMs,
    });
  }

  /**
   * Called by the app layer when the app returns to foreground.
   * If backgrounded, transitions back to running and emits
   * a foregrounded event with the duration of the background period.
   */
  public notifyForeground(): void {
    if (this.backgroundedAtMonotonicMs === null) {
      return;
    }
    const monotonicMs = this.monotonic.now();
    const backgroundedForMs = this.scaledDelta(this.backgroundedAtMonotonicMs, monotonicMs);
    this._totalBackgroundedMs += backgroundedForMs;
    this.backgroundedAtMonotonicMs = null;
    this.lastTickMonotonicMs = monotonicMs;
    this._state = 'running';

    this.emit({
      type: 'foregrounded',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      totalElapsedMs: this._totalActiveMs,
      backgroundedForMs,
    });

    this.scheduleNextTick();
  }

  // REDACTED
  // Public API — Configuration
  // REDACTED

  public setMode(mode: TimerMode): void {
    if (this._mode === mode) {
      return;
    }
    const previousMode = this._mode;
    this._mode = mode;
    this._tickIntervalMs = TIMER_MODE_TICK_INTERVAL_MS[mode];
    this.emit({
      type: 'mode-changed',
      monotonicMs: this.monotonic.now(),
      wallIso: this.wall.isoNow(),
      previousMode,
      currentMode: mode,
      tickIntervalMs: this._tickIntervalMs,
    });
    // No reschedule: next tick uses the new interval naturally.
  }

  public setTimeScale(scale: number): void {
    if (!isValidTimeScale(scale)) {
      throw new AppError(`Time scale must be in [${MIN_TIME_SCALE}, ${MAX_TIME_SCALE}]`, {
        code: 'timer_invalid_time_scale',
        severity: 'warn',
        context: { scale, min: MIN_TIME_SCALE, max: MAX_TIME_SCALE },
      });
    }
    if (this._timeScale === scale) {
      return;
    }
    const previousScale = this._timeScale;
    this._timeScale = scale;
    this.emit({
      type: 'time-scale-changed',
      monotonicMs: this.monotonic.now(),
      wallIso: this.wall.isoNow(),
      previousScale,
      currentScale: scale,
    });
  }

  // REDACTED
  // Public API — Subscription
  // REDACTED

  public subscribe(listener: TimerListener): Unsubscribe {
    return this.events.subscribe(listener);
  }

  // REDACTED
  // Public API — Read-only accessors
  // REDACTED

  public getState(): TimerState {
    return this._state;
  }

  public getMode(): TimerMode {
    return this._mode;
  }

  public getTimeScale(): number {
    return this._timeScale;
  }

  public getTickIntervalMs(): number {
    return this._tickIntervalMs;
  }

  public getTotalElapsedMs(): number {
    return this._totalActiveMs;
  }

  public getTotalPausedMs(): number {
    return this._totalPausedMs;
  }

  public getTotalBackgroundedMs(): number {
    return this._totalBackgroundedMs;
  }

  public getTickIndex(): number {
    return this._tickIndex;
  }

  public getSessionStartedAtWallIso(): string | null {
    return this.sessionStartedAtWallIso;
  }

  public snapshot(): TimerEngineSnapshot {
    return {
      state: this._state,
      mode: this._mode,
      timeScale: this._timeScale,
      tickIntervalMs: this._tickIntervalMs,
      totalElapsedMs: this._totalActiveMs,
      totalActiveMs: this._totalActiveMs,
      totalPausedMs: this._totalPausedMs,
      totalBackgroundedMs: this._totalBackgroundedMs,
      tickIndex: this._tickIndex,
      listenerCount: this.events.listenerCount(),
    };
  }

  // REDACTED
  // Internal — Tick scheduling
  // REDACTED

  private scheduleNextTick(): void {
    if (this._state !== 'running') {
      return;
    }
    const baseDelay = this._tickIntervalMs;
    const compensatedDelay = this.drift.computeNextDelayMs({
      intervalMs: baseDelay,
      previousDriftMs: this.lastDriftEmitted ? this.lastDriftMs : 0,
      previousNextDelayMs: baseDelay,
      actualElapsedMs: this._totalActiveMs,
    });
    this.activeHandle = this.clockProvider.setTimeout(() => {
      this.activeHandle = null;
      this.handleTick();
    }, compensatedDelay);
  }

  private handleTick(): void {
    if (this._state !== 'running') {
      return;
    }
    const monotonicMs = this.monotonic.now();

    if (this.lastTickMonotonicMs !== null) {
      this._totalActiveMs += this.scaledDelta(this.lastTickMonotonicMs, monotonicMs);
    }
    this.lastTickMonotonicMs = monotonicMs;
    this._tickIndex += 1;

    // Measure drift against expected elapsed since session start.
    const expectedElapsed = this._tickIndex * this._tickIntervalMs;
    const measurement: DriftMeasurement = {
      tickIndex: this._tickIndex,
      actualElapsedMs: this._totalActiveMs,
      expectedElapsedMs: expectedElapsed,
      driftMs: this._totalActiveMs - expectedElapsed,
      cumulativeDriftMs: 0, // Computed lazily by corrector; not used downstream.
    };

    this.emit({
      type: 'tick',
      monotonicMs,
      wallIso: this.wall.isoNow(),
      tickIndex: this._tickIndex,
      elapsedMs: this._totalActiveMs,
      totalElapsedMs: this._totalActiveMs,
    });

    const observation = this.drift.recordTick({
      tickIndex: this._tickIndex - 1,
      intervalMs: this._tickIntervalMs,
      actualElapsedMs: this._totalActiveMs,
    });
    if (observation !== null) {
      this.lastDriftMs = observation.driftMs;
      this.lastDriftEmitted = true;
      this.emit({
        type: 'drift',
        monotonicMs: this.monotonic.now(),
        wallIso: this.wall.isoNow(),
        measurement,
      });
    } else {
      this.lastDriftEmitted = false;
    }

    this.scheduleNextTick();
  }

  private emit(event: TimerEvent): void {
    this.events.emit(event);
  }

  private cancelActiveHandle(): void {
    if (this.activeHandle !== null) {
      this.activeHandle.cancel();
      this.activeHandle = null;
    }
  }

  private scaledDelta(fromMs: number, toMs: number): number {
    return Math.max(0, (toMs - fromMs) * this._timeScale);
  }
}
