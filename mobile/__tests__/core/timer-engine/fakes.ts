/**
 * Test fakes for the Timer Engine.
 *
 * These are NOT mocks — they are real working implementations that
 * give the test runner deterministic control over time. Used in
 * `__tests__/core/timer-engine/*` exclusively.
 *
 * Conventions:
 *   - `FakeMonotonicClock` — caller advances time via `advance(ms)`.
 *   - `FakeWallClock` — paired with FakeMonotonicClock; same `advance`.
 *   - `FakeClockProvider` — setTimeout/setInterval return handles
 *     that fire only when the test calls `runPending()` or `advance()`.
 *
 * The fakes model two kinds of "time":
 *   - "Virtual ms" — what the engine thinks happened.
 *   - "Real ms" — irrelevant in unit tests; we don't use real timers.
 */

import type {
  ClockCallback,
  ClockHandle,
  ClockProvider,
  MonotonicClock,
  WallClock,
} from '@core/timer-engine';

class FakeClockHandle implements ClockHandle {
  public cancelled = false;
  public fired = false;
  public callback: ClockCallback;
  public dueAtMs: number;
  public recurring: boolean;
  public periodMs: number;

  public constructor(callback: ClockCallback, dueAtMs: number, recurring: boolean, periodMs: number) {
    this.callback = callback;
    this.dueAtMs = dueAtMs;
    this.recurring = recurring;
    this.periodMs = periodMs;
  }

  public cancel(): void {
    this.cancelled = true;
  }

  public isActive(): boolean {
    return !this.cancelled && !this.fired;
  }
}

export class FakeMonotonicClock implements MonotonicClock {
  private current = 0;
  public constructor(initial = 0) {
    this.current = initial;
  }

  public now(): number {
    return this.current;
  }

  public advance(deltaMs: number): void {
    this.current += deltaMs;
  }

  public setAbsolute(ms: number): void {
    this.current = ms;
  }
}

export class FakeWallClock implements WallClock {
  private monotonic: FakeMonotonicClock;
  private baseEpochMs: number;
  public constructor(monotonic: FakeMonotonicClock, baseEpochMs = 1_700_000_000_000) {
    this.monotonic = monotonic;
    this.baseEpochMs = baseEpochMs;
  }

  public now(): number {
    return this.baseEpochMs + this.monotonic.now();
  }

  public isoNow(): string {
    return new Date(this.now()).toISOString();
  }
}

export interface FakeClockProviderOptions {
  readonly monotonic: FakeMonotonicClock;
  /**
   * If true, setTimeout callbacks fire automatically when the
   * monotonic clock advances past their due time during `advance()`.
   * If false, callers must call `runPending()` explicitly.
   * Default: true.
   */
  readonly autoFireOnAdvance?: boolean;
}

export class FakeClockProvider implements ClockProvider {
  private readonly monotonic: FakeMonotonicClock;
  private readonly handles: FakeClockHandle[] = [];
  private readonly autoFire: boolean;

  public constructor(options: FakeClockProviderOptions) {
    this.monotonic = options.monotonic;
    this.autoFire = options.autoFireOnAdvance ?? true;
  }

  public setTimeout(callback: ClockCallback, delayMs: number): ClockHandle {
    const handle = new FakeClockHandle(callback, this.monotonic.now() + delayMs, false, delayMs);
    this.handles.push(handle);
    return handle;
  }

  public setInterval(callback: ClockCallback, periodMs: number): ClockHandle {
    const handle = new FakeClockHandle(callback, this.monotonic.now() + periodMs, true, periodMs);
    this.handles.push(handle);
    return handle;
  }

  /**
   * Advances monotonic time and fires due callbacks. This is the
   * primary way tests drive the engine forward.
   *
   * The implementation advances in small steps when needed to ensure
   * due callbacks fire in chronological order.
   */
  public advance(deltaMs: number): void {
    if (deltaMs < 0) {
      return;
    }
    const target = this.monotonic.now() + deltaMs;
    while (this.monotonic.now() < target) {
      const activeHandles = this.handles.filter((h) => !h.cancelled && !h.fired);
      if (activeHandles.length === 0) {
        this.monotonic.setAbsolute(target);
        break;
      }
      const nextDue = activeHandles.reduce(
        (min, h) => (h.dueAtMs < min ? h.dueAtMs : min),
        Number.POSITIVE_INFINITY,
      );
      const step = Math.min(nextDue, target) - this.monotonic.now();
      if (step > 0) {
        this.monotonic.advance(step);
      }
      const due = this.handles
        .filter((h) => !h.cancelled && !h.fired && h.dueAtMs <= this.monotonic.now())
        .sort((a, b) => a.dueAtMs - b.dueAtMs);
      for (const handle of due) {
        if (handle.cancelled || handle.fired) {
          continue;
        }
        handle.fired = true;
        try {
          handle.callback();
        } catch {
          // Errors in callbacks must not break the test runner.
        }
        if (handle.recurring && !handle.cancelled) {
          handle.fired = false;
          handle.dueAtMs = this.monotonic.now() + handle.periodMs;
        }
      }
      if (!this.autoFire && this.monotonic.now() < target) {
        // No more callbacks will fire this round; jump to target.
        this.monotonic.setAbsolute(target);
        break;
      }
    }
  }

  /**
   * Runs all currently-pending callbacks without advancing time.
   * Useful when a test wants to drain the queue explicitly.
   */
  public runPending(): void {
    const due = this.handles
      .filter((h) => !h.cancelled && !h.fired && h.dueAtMs <= this.monotonic.now())
      .sort((a, b) => a.dueAtMs - b.dueAtMs);
    for (const handle of due) {
      if (handle.cancelled || handle.fired) {
        continue;
      }
      handle.fired = true;
      try {
        handle.callback();
      } catch {
        // ignore
      }
      if (handle.recurring && !handle.cancelled) {
        handle.fired = false;
        handle.dueAtMs = this.monotonic.now() + handle.periodMs;
      }
    }
  }

  /**
   * Number of active (not cancelled, not fired) handles.
   */
  public activeHandleCount(): number {
    return this.handles.filter((h) => !h.cancelled && !h.fired).length;
  }

  /**
   * Cancels all pending handles. Useful in test teardown.
   */
  public cancelAll(): void {
    for (const h of this.handles) {
      h.cancel();
    }
  }
}

export interface TimerTestRig {
  readonly engine: import('@core/timer-engine').TimerEngine;
  readonly monotonic: FakeMonotonicClock;
  readonly wall: FakeWallClock;
  readonly clock: FakeClockProvider;
  readonly events: import('@core/timer-engine').TimerEvent[];
  unsubscribe: () => void;
  reset(): void;
}

export const createTimerTestRig = (mode: import('@core/timer-engine').TimerMode = 'balanced'): TimerTestRig => {
  const monotonic = new FakeMonotonicClock();
  const wall = new FakeWallClock(monotonic);
  const clock = new FakeClockProvider({ monotonic });
  const engine = new (require('@core/timer-engine').TimerEngine)({
    monotonic,
    wall,
    clockProvider: clock,
    mode,
  });
  const events: import('@core/timer-engine').TimerEvent[] = [];
  const unsubscribe = engine.subscribe((e) => {
    events.push(e);
  });
  return {
    engine,
    monotonic,
    wall,
    clock,
    events,
    unsubscribe,
    reset: (): void => {
      events.length = 0;
    },
  };
};
