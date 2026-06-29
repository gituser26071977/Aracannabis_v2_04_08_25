/**
 * RuntimeEngineDeps — constructor options for `createRuntimeEngine`.
 *
 * The Runtime owns the 3 frozen engines internally (TimerEngine,
 * BreathEngine created lazily, ProtocolRuntime). The factory wires
 * them based on these options.
 *
 * Callers that need to override clock behavior (e.g. for testing) can
 * pass custom timers via `timerEngine`. Production callers omit it
 * and let the Runtime create default browser timers.
 */

import type { EngineId } from '@araflow/shared-contracts';

import type { TimerEngine } from '@core/timer-engine';

import type { RuntimeEventListener } from '../domain/RuntimeEvent';

export interface RuntimeEngineDeps {
  /** Required — branded engine id used in events / logs. */
  readonly runtimeId: EngineId;

  /**
   * Optional pre-built TimerEngine. If omitted, the Runtime creates
   * a default TimerEngine with browser clocks. Provided mainly for
   * tests that want to inject a FakeTimer; production callers omit.
   */
  readonly timerEngine?: TimerEngine;

  /**
   * Optional listener error sink. Invoked when a subscriber throws.
   * If omitted, listener exceptions are silently swallowed (events
   * are still delivered to other listeners).
   */
  readonly onListenerError?: (error: unknown, listener: RuntimeEventListener) => void;
}
