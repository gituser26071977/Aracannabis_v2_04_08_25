/**
 * TimerLike adapter — wraps a TimerEngine so it satisfies the
 * `TimerLike` interface required by `ProtocolRuntime`.
 *
 * Moved from `tools/araflow-cli/src/adapters/timer-like.ts` (Sprint 3.5)
 * into Core as part of Sprint 4 — the adapter is structurally part of
 * the Runtime's wiring, not CLI-internal.
 *
 * Adapter is intentionally minimal — TimerEngine already exposes
 * `start`, `stop`, `subscribe`, `getTotalElapsedMs`. The only
 * transformation is narrowing TimerEvent (with many fields) to
 * TimerLikeEvent (just `type` + `monotonicMs`).
 *
 * ProtocolRuntime uses only `tick` events but we pass through all
 * events and let the runtime filter internally (it ignores non-'tick').
 */

import type { TimerLike, TimerLikeEvent } from '@core/protocol-compiler';
import type { TimerEngine } from '@core/timer-engine';

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
