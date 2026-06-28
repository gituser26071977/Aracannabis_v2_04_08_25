/**
 * DefaultClockProvider — implementa ClockProvider sobre
 * setTimeout/setInterval nativos.
 *
 * O handle retornado é cancelável e idempotente. Usamos uma classe
 * interna (RealHandle) que envolve o handle nativo.
 *
 * Compatibilidade: qualquer runtime que exponha setTimeout/setInterval
 * com a semântica padrão W3C/ECMA-262. Isso inclui React Native,
 * Browsers, Node, Bun, Deno.
 *
 * Edge case: em React Native, se o JS thread é suspenso (app em
 * background), os timers podem acumular e disparar todos juntos
 * quando o thread retomar. A DriftCorrector compensa quando
 * possível; o Timer Engine também recebe `notifyBackground()` /
 * `notifyForeground()` para controle explícito.
 */

import type { ClockCallback, ClockHandle, ClockProvider } from '../domain';

class RealHandle implements ClockHandle {
  private native: ReturnType<typeof setTimeout> | null;
  private cancelled = false;
  private fired = false;

  public constructor(native: ReturnType<typeof setTimeout>) {
    this.native = native;
  }

  public cancel(): void {
    if (this.cancelled || this.fired) {
      return;
    }
    if (this.native !== null) {
      clearTimeout(this.native);
    }
    this.cancelled = true;
    this.native = null;
  }

  public isActive(): boolean {
    return !this.cancelled && !this.fired;
  }

  public markFired(): void {
    this.fired = true;
    this.native = null;
  }
}

class RealIntervalHandle implements ClockHandle {
  private native: ReturnType<typeof setInterval> | null;
  private cancelled = false;

  public constructor(native: ReturnType<typeof setInterval>) {
    this.native = native;
  }

  public cancel(): void {
    if (this.cancelled) {
      return;
    }
    if (this.native !== null) {
      clearInterval(this.native);
    }
    this.cancelled = true;
    this.native = null;
  }

  public isActive(): boolean {
    return !this.cancelled;
  }
}

export interface DefaultClockProviderOptions {
  /**
   * Override the setTimeout function (useful for testing with mocks
   * without changing the public API of ClockProvider).
   * Defaults to globalThis.setTimeout.
   */
  readonly setTimeoutFn?: typeof setTimeout;
  /**
   * Override the setInterval function. Defaults to globalThis.setInterval.
   */
  readonly setIntervalFn?: typeof setInterval;
  /**
   * Override the clearTimeout function. Defaults to globalThis.clearTimeout.
   */
  readonly clearTimeoutFn?: typeof clearTimeout;
  /**
   * Override the clearInterval function. Defaults to globalThis.clearInterval.
   */
  readonly clearIntervalFn?: typeof clearInterval;
}

const resolveGlobal = <T extends (...args: never[]) => unknown>(name: string, fallback: T): T => {
  if (typeof globalThis === 'undefined') {
    return fallback;
  }
  const value = (globalThis as Record<string, unknown>)[name];
  if (typeof value === 'function') {
    return value as T;
  }
  return fallback;
};

export const createDefaultClockProvider = (
  options: DefaultClockProviderOptions = {},
): ClockProvider => {
  const setTimeoutFn = options.setTimeoutFn ?? resolveGlobal<typeof setTimeout>('setTimeout', setTimeout);
  const setIntervalFn = options.setIntervalFn ?? resolveGlobal<typeof setInterval>('setInterval', setInterval);

  return {
    setTimeout: (callback: ClockCallback, delayMs: number): ClockHandle => {
      const handle = new RealHandle(undefined as unknown as ReturnType<typeof setTimeout>);
      const native = setTimeoutFn(() => {
        handle.markFired();
        callback();
      }, delayMs);
      // Replace placeholder with actual native handle.
      (handle as unknown as { native: ReturnType<typeof setTimeout> }).native = native;
      return handle;
    },
    setInterval: (callback: ClockCallback, periodMs: number): ClockHandle => {
      const native = setIntervalFn(callback, periodMs);
      return new RealIntervalHandle(native);
    },
  };
};
