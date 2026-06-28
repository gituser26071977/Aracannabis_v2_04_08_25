/**
 * BreathEngine — orquestrador da mecânica respiratória.
 *
 * Responsabilidades:
 *   - Coordenar fases dentro de um ciclo.
 *   - Coordenar múltiplos ciclos.
 *   - Computar profundidade (depth) usando a curva configurada.
 *   - Detectar transições e emitir eventos.
 *   - Responder a interrupções do app (background/foreground).
 *   - Permitir cancelamento manual.
 *
 * NÃO é responsável por:
 *   - Conhecimento clínico (Box Breathing, 4-7-8, ansiedade, insônia).
 *   - Animação visual.
 *   - Áudio.
 *   - Persistência.
 *
 * Princípios:
 *   - Determinístico: dado o mesmo TimerEngine e config, comportamento é reproduzível.
 *   - Re-entrante: chamada de cancel/subscribe durante dispatch é tratada corretamente.
 *   - Thread-safe (JS single-threaded).
 *   - Sem dependência de UI, React, RN, plataforma.
 *
 * Integração com Timer Engine:
 *   - Subscreve ao TimerEngine para receber tick events.
 *   - Captura `getTotalElapsedMs()` no start como baseline.
 *   - Em cada tick, calcula delta da baseline para obter sessionElapsedMs.
 *   - Reage a `backgrounded`/`foregrounded` para entrar/sair do estado interrupted.
 *
 * IMPORTANTE: Breath Engine NÃO controla o ciclo de vida do Timer Engine.
 * O caller é responsável por iniciar o Timer Engine antes do Breath Engine.
 */

import {
  TimerEngine,
  type MonotonicClock,
  type TimerEvent,
} from '@core/timer-engine';

import { AppError } from '@shared/errors';

import type {
  BreathCycleConfig,
  BreathListener,
  BreathPhase,
  BreathSnapshot,
  BreathUnsubscribe,
  CurveFn,
  CurveName,
} from '../domain';
import {
  DEFAULT_CURVE_NAME,
  EMPTY_BREATH_SNAPSHOT,
  isActiveBreathState,
  isTerminalBreathState,
  resolveCurve,
  validateBreathCycleConfig,
} from '../domain';
import { computeDepth } from './DepthCalculator';
import type { PhaseInfo } from './PhaseCalculator';
import { computePhaseInfo } from './PhaseCalculator';
import {
  createBreathEventDispatcher,
  type BreathEventDispatcher,
} from './EventDispatcher';

export interface BreathEngineDeps {
  readonly monotonic: MonotonicClock;
  readonly timerEngine: TimerEngine;
  readonly config: BreathCycleConfig;
  readonly curve?: CurveFn;
  readonly curveName?: CurveName;
  readonly onListenerError?: (error: unknown, listener: BreathListener) => void;
}

const INITIAL_CYCLE_INDEX = 0;

export class BreathEngine {
  private readonly monotonic: MonotonicClock;
  private readonly timerEngine: TimerEngine;
  private readonly config: BreathCycleConfig;
  private readonly curve: CurveFn;
  private readonly curveName: string;
  private readonly events: BreathEventDispatcher;
  private readonly unsubscribeFromTimer: () => void;

  private _state: import('../domain').BreathState = 'idle';
  private _sessionStartedAtMonotonicMs: number | null = null;
  private _sessionStartedAtTimerElapsedMs: number = 0;
  private _sessionElapsedMs: number = 0;
  private _lastPhase: BreathPhase | null = null;
  private _lastCycleIndex: number = 0;
  private _cyclesCompleted: number = 0;
  private _currentPhase: BreathPhase | null = null;
  private _lastSnapshot: BreathSnapshot = EMPTY_BREATH_SNAPSHOT;

  public constructor(deps: BreathEngineDeps) {
    if (deps.monotonic === undefined) {
      throw new AppError('BreathEngine requires monotonic clock', {
        code: 'breath_missing_dependency',
        severity: 'fatal',
      });
    }
    if (deps.timerEngine === undefined) {
      throw new AppError('BreathEngine requires timerEngine', {
        code: 'breath_missing_dependency',
        severity: 'fatal',
      });
    }
    validateBreathCycleConfig(deps.config);

    this.monotonic = deps.monotonic;
    this.timerEngine = deps.timerEngine;
    this.config = deps.config;
    this.curveName = deps.curveName ?? DEFAULT_CURVE_NAME;
    this.curve = deps.curve ?? resolveCurve(this.curveName);
    this.events = createBreathEventDispatcher(deps.onListenerError);

    // Capture reference for disposal; subscribe once.
    this.unsubscribeFromTimer = this.timerEngine.subscribe(this.handleTimerEvent);
  }

  // REDACTED
  // Public API — Lifecycle
  // REDACTED

  /**
   * Starts a breath session. Idempotent no-op in active states. Throws
   * AppError when called from terminal-but-unresettable states.
   *
   * Caller must ensure the Timer Engine is running before calling start.
   * If Timer Engine is not running, ticks won't fire and the session
   * will not progress.
   */
  public start(): void {
    if (this._state !== 'idle' && this._state !== 'completed' && this._state !== 'cancelled') {
      throw new AppError('Cannot start: breath engine is already active', {
        code: 'breath_invalid_state',
        severity: 'warn',
        context: { state: this._state },
      });
    }

    const timerState = this.timerEngine.getState();
    if (timerState !== 'running') {
      throw new AppError(
        'BreathEngine requires TimerEngine to be running; caller must start it first',
        {
          code: 'breath_timer_not_running',
          severity: 'warn',
          context: { timerState },
        },
      );
    }

    const now = this.monotonic.now();
    const sessionDuration = this.sessionDurationMs();
    this._sessionStartedAtMonotonicMs = now;
    this._sessionStartedAtTimerElapsedMs = this.timerEngine.getTotalElapsedMs();
    this._sessionElapsedMs = 0;
    this._cyclesCompleted = 0;
    this._lastPhase = null;
    this._lastCycleIndex = INITIAL_CYCLE_INDEX;
    this._currentPhase = null;

    const prepMs = this.config.prepMs ?? 0;
    if (prepMs > 0) {
      this._state = 'preparing';
    } else {
      this._state = 'inhaling';
      this._currentPhase = 'inhaling';
      this._lastPhase = 'inhaling';
    }

    this.events.emit({
      type: 'breath-started',
      monotonicMs: now,
      totalCycles: this.config.cycles,
      totalDurationMs: sessionDuration,
    });

    // For prepMs=0 case, emit the first cycle-started and phase-changed
    // immediately so UI receives the transition in the same frame as start.
    if (prepMs === 0) {
      this.events.emit({
        type: 'cycle-started',
        monotonicMs: now,
        cycleIndex: INITIAL_CYCLE_INDEX,
        totalCycles: this.config.cycles,
      });
      this.events.emit({
        type: 'phase-changed',
        monotonicMs: now,
        previousPhase: null,
        currentPhase: 'inhaling',
        cycleIndex: INITIAL_CYCLE_INDEX,
        phaseProgress: 0,
      });
    }

    this.refreshSnapshot();
  }

  /**
   * Cancels the active session. No-op if already terminal/idle.
   */
  public cancel(): void {
    if (this._state === 'idle' || isTerminalBreathState(this._state)) {
      return;
    }
    const stateBefore = this._state;
    const now = this.monotonic.now();
    this._state = 'cancelled';
    this._currentPhase = null;
    this._lastPhase = null;
    this.events.emit({
      type: 'cancelled',
      monotonicMs: now,
      stateBefore,
      elapsedAtCancelMs: this._sessionElapsedMs,
      cyclesCompleted: this._cyclesCompleted,
    });
    this.refreshSnapshot();
  }

  /**
   * Resets the engine to idle state. Wipes all session state. Does NOT
   * reset the Timer Engine.
   */
  public reset(): void {
    this._state = 'idle';
    this._sessionStartedAtMonotonicMs = null;
    this._sessionStartedAtTimerElapsedMs = 0;
    this._sessionElapsedMs = 0;
    this._lastPhase = null;
    this._lastCycleIndex = 0;
    this._cyclesCompleted = 0;
    this._currentPhase = null;
    this._lastSnapshot = {
      ...EMPTY_BREATH_SNAPSHOT,
      totalCycles: this.config.cycles,
    };
  }

  // REDACTED
  // Public API — Subscription
  // REDACTED

  public subscribe(listener: BreathListener): BreathUnsubscribe {
    return this.events.subscribe(listener);
  }

  // REDACTED
  // Public API — Read-only accessors
  // REDACTED

  public getState(): import('../domain').BreathState {
    return this._state;
  }

  public getCurrentPhase(): BreathPhase | null {
    return this._currentPhase;
  }

  public getCyclesCompleted(): number {
    return this._cyclesCompleted;
  }

  public getSessionElapsedMs(): number {
    return this._sessionElapsedMs;
  }

  public getConfig(): BreathCycleConfig {
    return this.config;
  }

  public getCurveName(): string {
    return this.curveName;
  }

  public snapshot(): BreathSnapshot {
    return this._lastSnapshot;
  }

  // REDACTED
  // Public API — Cleanup
  // REDACTED

  public dispose(): void {
    this.unsubscribeFromTimer();
    this.events.clear();
  }

  // REDACTED
  // Internal — Timer Engine event handling
  // REDACTED

  private handleTimerEvent = (event: TimerEvent): void => {
    switch (event.type) {
      case 'tick':
        if (isActiveBreathState(this._state)) {
          this.handleTick(event.totalElapsedMs);
        }
        return;
      case 'backgrounded':
        if (isActiveBreathState(this._state)) {
          this.handleBackground();
        }
        return;
      case 'foregrounded':
        if (this._state === 'interrupted') {
          this.handleForeground(event.backgroundedForMs);
        }
        return;
      default:
        return;
    }
  };

  private handleTick(totalElapsedMs: number): void {
    if (!isActiveBreathState(this._state)) {
      return;
    }
    const sessionElapsedMs = Math.max(0, totalElapsedMs - this._sessionStartedAtTimerElapsedMs);
    this._sessionElapsedMs = sessionElapsedMs;

    const totalDuration = this.totalDurationMs();
    if (sessionElapsedMs >= totalDuration) {
      this.completeSession();
      return;
    }

    const phaseInfo = computePhaseInfo(this.config, sessionElapsedMs);
    this.processTransitions(phaseInfo);
    this.refreshSnapshot(phaseInfo);
  }

  private processTransitions(phaseInfo: PhaseInfo): void {
    const now = this.monotonic.now();

    // Cycle boundary detection.
    if (phaseInfo.cycleIndex !== this._lastCycleIndex) {
      const previousCycleIndex = this._lastCycleIndex;

      // Emit cycle-completed for the cycle that just finished (if valid).
      if (previousCycleIndex >= 0 && previousCycleIndex < this.config.cycles) {
        this._cyclesCompleted = previousCycleIndex + 1;
        this.events.emit({
          type: 'cycle-completed',
          monotonicMs: now,
          cycleIndex: previousCycleIndex,
          totalCycles: this.config.cycles,
        });
      }

      // Emit cycle-started for the new cycle (if not past the end).
      if (phaseInfo.cycleIndex < this.config.cycles) {
        this.events.emit({
          type: 'cycle-started',
          monotonicMs: now,
          cycleIndex: phaseInfo.cycleIndex,
          totalCycles: this.config.cycles,
        });
      }

      this._lastCycleIndex = phaseInfo.cycleIndex;
    }

    // Phase boundary detection.
    if (phaseInfo.phase !== this._lastPhase) {
      const previousPhase = this._lastPhase;

      // Special transition: preparing → first inhaling. Emit breath-started
      // semantics via cycle-started(0) which we may have missed at start().
      if (previousPhase === null && phaseInfo.phase !== null) {
        if (this._state === 'preparing') {
          this._state = 'inhaling';
          if (phaseInfo.cycleIndex === 0 && this._lastCycleIndex === 0 && this._cyclesCompleted === 0) {
            // We delayed the first cycle-started until prepMs elapsed.
            this.events.emit({
              type: 'cycle-started',
              monotonicMs: now,
              cycleIndex: INITIAL_CYCLE_INDEX,
              totalCycles: this.config.cycles,
            });
          }
        }
      }

      // Special transition: exhaling → holdAfterExhale (or → next inhaling
      // when holdAfterExhaleMs=0). Emit breath-completed.
      if (previousPhase === 'exhaling' &&
          (phaseInfo.phase === 'holdAfterExhale' || phaseInfo.phase === 'inhaling')) {
        this.events.emit({
          type: 'breath-completed',
          monotonicMs: now,
          cycleIndex: phaseInfo.cycleIndex,
          totalCycles: this.config.cycles,
        });
      }

      // Update state machine to the new phase (if active).
      if (phaseInfo.phase !== null) {
        this._state = phaseInfo.phase;
        this._currentPhase = phaseInfo.phase;
      }

      this.events.emit({
        type: 'phase-changed',
        monotonicMs: now,
        previousPhase,
        currentPhase: phaseInfo.phase,
        cycleIndex: phaseInfo.cycleIndex,
        phaseProgress: phaseInfo.phaseProgress,
      });

      this._lastPhase = phaseInfo.phase;
    }
  }

  private completeSession(): void {
    const now = this.monotonic.now();

    // If the last cycle wasn't explicitly emitted as completed (the tick
    // boundary crossed past sessionDurationMs), emit it now.
    if (this._lastCycleIndex < this.config.cycles && this._cyclesCompleted < this.config.cycles) {
      this._cyclesCompleted = this.config.cycles;
      this.events.emit({
        type: 'cycle-completed',
        monotonicMs: now,
        cycleIndex: this.config.cycles - 1,
        totalCycles: this.config.cycles,
      });
    }

    this._state = 'completed';
    this._currentPhase = null;
    this._lastPhase = null;
    this.events.emit({
      type: 'completed',
      monotonicMs: now,
      totalCycles: this.config.cycles,
      totalElapsedMs: this._sessionElapsedMs,
    });
    this.refreshSnapshot();
  }

  private handleBackground(): void {
    if (!isActiveBreathState(this._state)) {
      return;
    }
    const stateBefore = this._state;
    const now = this.monotonic.now();
    this._state = 'interrupted';
    this._currentPhase = null;
    this.events.emit({
      type: 'interrupted',
      monotonicMs: now,
      stateBefore,
      elapsedAtInterruptionMs: this._sessionElapsedMs,
    });
    this.refreshSnapshot();
  }

  private handleForeground(interruptedForMs: number): void {
    if (this._state !== 'interrupted') {
      return;
    }
    const stateBefore = this._state;
    const now = this.monotonic.now();

    // Determine what phase we should resume to based on sessionElapsedMs.
    const phaseInfo = computePhaseInfo(this.config, this._sessionElapsedMs);
    let resumedPhase: BreathPhase | null;
    let resumedCycleIndex: number;

    if (phaseInfo.activity === 'preparing') {
      this._state = 'preparing';
      resumedPhase = null;
      resumedCycleIndex = 0;
    } else if (phaseInfo.activity === 'completed') {
      // Session actually completed during background (shouldn't happen because
      // Timer Engine pauses elapsed time during background, but handle anyway).
      this._state = 'completed';
      resumedPhase = null;
      resumedCycleIndex = this.config.cycles;
      this.events.emit({
        type: 'completed',
        monotonicMs: now,
        totalCycles: this.config.cycles,
        totalElapsedMs: this._sessionElapsedMs,
      });
    } else {
      this._state = phaseInfo.phase as BreathPhase;
      resumedPhase = phaseInfo.phase;
      resumedCycleIndex = phaseInfo.cycleIndex;
    }

    this._currentPhase = resumedPhase;
    this._lastPhase = resumedPhase;
    this._lastCycleIndex = resumedCycleIndex;

    this.events.emit({
      type: 'resumed-from-interrupt',
      monotonicMs: now,
      stateBefore,
      interruptedForMs,
      resumedPhase,
      resumedCycleIndex,
    });
    this.refreshSnapshot();
  }

  private refreshSnapshot(phaseInfo?: PhaseInfo): void {
    const info = phaseInfo ?? computePhaseInfo(this.config, this._sessionElapsedMs);
    const depth = computeDepth(this._currentPhase, info.phaseProgress, this.curve);
    this._lastSnapshot = {
      state: this._state,
      phase: this._currentPhase,
      cycleIndex: info.cycleIndex,
      totalCycles: this.config.cycles,
      cycleProgress: info.cycleProgress,
      phaseProgress: info.phaseProgress,
      phaseElapsedMs: info.phaseElapsedMs,
      phaseRemainingMs: info.phaseRemainingMs,
      totalElapsedMs: this._sessionElapsedMs,
      totalRemainingMs: info.totalRemainingMs,
      depth,
      curveName: this.curveName,
    };
  }

  private totalDurationMs(): number {
    return (this.config.prepMs ?? 0) + this.sessionDurationMs();
  }

  private sessionDurationMs(): number {
    const cycle = this.config.inhaleMs + this.config.holdAfterInhaleMs +
                  this.config.exhaleMs + this.config.holdAfterExhaleMs;
    return cycle * this.config.cycles;
  }
}