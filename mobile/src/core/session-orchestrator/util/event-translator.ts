/**
 * event-translator — pure projection from RuntimeEvent into a typed
 * SessionAction. The Orchestrator uses this translator to decide
 * what to do with each Runtime event.
 *
 * Mapping table (only Protocol + Runtime channels are translated;
 * Timer and Breath channels are engine-level noise to the Session):
 *
 *   protocol-runtime-started             → session.start()
 *   protocol-runtime-paused              → session.pause()
 *   protocol-runtime-resumed             → session.resume()
 *   protocol-runtime-phase-changed       → session.recordPhaseChange(...)
 *   protocol-runtime-cycle-completed     → session.recordCycleCompleted(...)
 *   protocol-runtime-completed           → session.complete()
 *   protocol-runtime-stopped(cancelled)  → session.cancel()
 *   protocol-runtime-stopped(errored)    → session.fail(...)
 *   protocol-runtime-errored             → session.fail(...)
 *   runtime-compile-failed               → session.fail(...)
 *   runtime-error                        → session.fail(...)
 *   runtime-completed                    → session.complete() (idempotent)
 *   runtime-disposed                     → session.dispose()
 *
 *   timer-*  / breath-*                  → skip (no Session action)
 *
 * The translator is pure: it does not touch Session state. It only
 * returns a typed action descriptor.
 */

import type { RuntimeEvent } from '@core/runtime';

export type SessionAction =
  | { readonly kind: 'start' }
  | { readonly kind: 'pause' }
  | { readonly kind: 'resume' }
  | { readonly kind: 'complete' }
  | { readonly kind: 'cancel'; readonly reason: string }
  | { readonly kind: 'fail'; readonly code: string; readonly message: string }
  | {
      readonly kind: 'recordPhaseChange';
      readonly phase: string;
      readonly cycleIndex: number;
      readonly phaseIndex: number;
      readonly phaseElapsedMs: number;
      readonly phaseDurationMs: number;
      readonly monotonicMs: number;
    }
  | {
      readonly kind: 'recordCycleCompleted';
      readonly cycleIndex: number;
      readonly cycleElapsedMs: number;
      readonly totalCycles: number;
      readonly monotonicMs: number;
    }
  | { readonly kind: 'dispose' }
  | { readonly kind: 'skip'; readonly reason: string };

export const translateRuntimeEvent = (event: RuntimeEvent): SessionAction => {
  if (event.source === 'timer' || event.source === 'breath') {
    return { kind: 'skip', reason: 'engine-level event not translated' };
  }

  if (event.source === 'protocol') {
    const payload = event.payload;
    switch (payload.type) {
      case 'protocol-runtime-started':
        return { kind: 'start' };
      case 'protocol-runtime-paused':
        return { kind: 'pause' };
      case 'protocol-runtime-resumed':
        return { kind: 'resume' };
      case 'protocol-runtime-phase-changed':
        return {
          kind: 'recordPhaseChange',
          phase: payload.currentPhase,
          cycleIndex: payload.cycleIndex,
          phaseIndex: 0,
          phaseElapsedMs: 0,
          phaseDurationMs: 0,
          monotonicMs: payload.monotonicMs,
        };
      case 'protocol-runtime-cycle-completed':
        return {
          kind: 'recordCycleCompleted',
          cycleIndex: payload.cycleIndex,
          cycleElapsedMs: 0,
          totalCycles: 0,
          monotonicMs: payload.monotonicMs,
        };
      case 'protocol-runtime-completed':
        return { kind: 'complete' };
      case 'protocol-runtime-stopped':
        if (payload.reason === 'errored') {
          return {
            kind: 'fail',
            code: 'runtime_stopped_errored',
            message: 'Runtime reported errored stop',
          };
        }
        if (payload.reason === 'cancelled') {
          return { kind: 'cancel', reason: 'runtime_stopped_cancelled' };
        }
        return { kind: 'skip', reason: `protocol-runtime-stopped(${payload.reason}) ignored` };
      case 'protocol-runtime-errored':
        return {
          kind: 'fail',
          code: payload.code,
          message: payload.message,
        };
      case 'protocol-runtime-tick':
        return { kind: 'skip', reason: 'tick is high-frequency; not translated' };
      default: {
        // Exhaustive check — unknown event type is a programmer error.
        const unknown: never = payload;
        return { kind: 'skip', reason: `unknown protocol event: ${String(unknown)}` };
      }
    }
  }

  // event.source === 'runtime'
  const payload = event.payload;
  switch (payload.type) {
    case 'runtime-warnings':
      return { kind: 'skip', reason: 'compile warnings are not a lifecycle event' };
    case 'runtime-compile-failed':
      // Runtime-level concern; Session was never started so there is
      // nothing to fail. Consistency check logs it as a divergence
      // if the Session is past idle.
      return {
        kind: 'skip',
        reason: 'runtime-compile-failed does not affect an idle Session',
      };
    case 'runtime-error':
      return {
        kind: 'fail',
        code: payload.code,
        message: payload.message,
      };
    case 'runtime-disposed':
      return { kind: 'dispose' };
    case 'runtime-completed':
      return { kind: 'complete' };
    default: {
      const unknown: never = payload;
      return { kind: 'skip', reason: `unknown runtime lifecycle event: ${String(unknown)}` };
    }
  }
};
