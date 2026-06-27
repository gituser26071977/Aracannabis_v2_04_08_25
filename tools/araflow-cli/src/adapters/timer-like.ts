/**
 * TimerLike adapter — wraps a TimerEngine so it satisfies the
 * `TimerLike` interface required by `ProtocolRuntime`.
 *
 * The adapter is intentionally minimal (~15 lines) — TimerEngine
 * already exposes `start`, `stop`, `subscribe`, and `getTotalElapsedMs`
 * structurally. The only transformation is narrowing TimerEvent
 * (with many fields) to TimerLikeEvent (with just `type` + `monotonicMs`).
 *
 * The ProtocolRuntime uses only `tick` events but we pass through all
 * events and let the runtime filter internally (it ignores non-'tick').
 *
 * Why this lives in the CLI:
 *   - The engines are FROZEN. TimerLike was defined by the compiler.
 *   - Adapters live in the consumer, not the producer.
 *   - This file proves the architectural seam is clean: zero engine
 *     changes were needed to wire TimerEngine → ProtocolRuntime.
 */

import type { TimerEngine } from '@core/timer-engine';
import type { TimerLike, TimerLikeEvent } from '@core/protocol-compiler';

export const createTimerLikeAdapter = (engine: TimerEngine): TimerLike => ({
  start: (): void => {
    engine.start();
  },
  stop: (): void => {
    engine.stop();
  },
  subscribe: (listener) =>
    engine.subscribe((event) => {
      const narrowed: TimerLikeEvent = {
        type: event.type,
        monotonicMs: event.monotonicMs,
      };
      listener(narrowed);
    }),
  getTotalElapsedMs: (): number => engine.getTotalElapsedMs(),
});
