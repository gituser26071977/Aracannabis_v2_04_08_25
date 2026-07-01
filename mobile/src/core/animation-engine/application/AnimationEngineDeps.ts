/**
 * AnimationEngineDeps — constructor options for the Animation Engine.
 *
 * The Engine consumes Runtime events by default. Breath and Session are
 * optional but recommended for richer synchronization. Timer is also
 * optional — when provided, the Engine subscribes to its ticks for
 * drift-free real-time updates.
 *
 * No UI / rendering dependencies. All inputs are Core engine APIs.
 */

import type { BreathEngine } from '@core/breath-engine';
import type { ExecutionSession } from '@core/execution-session';
import type { RuntimeEngine } from '@core/runtime';
import type { TimerEngine } from '@core/timer-engine';

import type { AnimationConfig } from '../domain/AnimationConfig';

export interface AnimationEngineDeps {
  readonly runtime: RuntimeEngine;
  readonly breath?: BreathEngine;
  readonly timer?: TimerEngine;
  readonly session?: ExecutionSession;
  readonly config?: AnimationConfig;
  /** Monotonic clock (defaults to Date.now). */
  readonly now?: () => number;
  /** Listener error sink. */
  readonly onListenerError?: (err: unknown, context: { readonly phase: string }) => void;
}
