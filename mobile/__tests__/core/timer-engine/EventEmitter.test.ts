/**
 * EventEmitter tests.
 *
 * Coverage:
 *   - subscribe / unsubscribe
 *   - emit dispatches to all listeners
 *   - emit is synchronous
 *   - re-entrant: subscribe/unsubscribe during dispatch
 *   - error in one listener does not break others
 *   - clear() removes all listeners
 */

import { createEventDispatcher } from '@core/timer-engine';

describe('EventEmitter', () => {
  it('dispatches events to all subscribers', () => {
    const emitter = createEventDispatcher();
    const received: string[] = [];
    emitter.subscribe((e) => {
      received.push(`a:${e.type}`);
    });
    emitter.subscribe((e) => {
      received.push(`b:${e.type}`);
    });
    emitter.emit({ type: 'started' as never, monotonicMs: 0, wallIso: '' });
    expect(received).toEqual(['a:started', 'b:started']);
  });

  it('returns an unsubscribe function that removes the listener', () => {
    const emitter = createEventDispatcher();
    const received: string[] = [];
    const off = emitter.subscribe((e) => {
      received.push(e.type);
    });
    emitter.emit({ type: 'started' as never, monotonicMs: 0, wallIso: '' });
    off();
    emitter.emit({ type: 'started' as never, monotonicMs: 0, wallIso: '' });
    expect(received).toEqual(['started']);
  });

  it('listenerCount reflects active listeners', () => {
    const emitter = createEventDispatcher();
    expect(emitter.listenerCount()).toBe(0);
    const off1 = emitter.subscribe(() => undefined);
    expect(emitter.listenerCount()).toBe(1);
    emitter.subscribe(() => undefined);
    expect(emitter.listenerCount()).toBe(2);
    off1();
    expect(emitter.listenerCount()).toBe(1);
  });

  it('handles re-entrant subscribe/unsubscribe during dispatch', () => {
    const emitter = createEventDispatcher();
    const order: string[] = [];
    const off2 = (): void => undefined;
    let handle: (() => void) | null = null;
    emitter.subscribe((e) => {
      order.push('l1');
      if (handle === null) {
        handle = emitter.subscribe((e2) => {
          order.push(`l2:${e2.type}`);
        });
      }
    });
    const unsub2 = emitter.subscribe((e) => {
      order.push('l2-orig');
      off2();
    });
    void unsub2;
    emitter.emit({ type: 'tick' as never, monotonicMs: 0, wallIso: '' });
    expect(order).toEqual(['l1', 'l2-orig', 'l2:tick']);
  });

  it('does not dispatch to listeners removed during emit', () => {
    const emitter = createEventDispatcher();
    const received: string[] = [];
    const off = emitter.subscribe((e) => {
      received.push(e.type);
      off();
    });
    emitter.emit({ type: 'first' as never, monotonicMs: 0, wallIso: '' });
    emitter.emit({ type: 'second' as never, monotonicMs: 0, wallIso: '' });
    expect(received).toEqual(['first']);
  });

  it('captures errors in listener and continues dispatch', () => {
    const errors: unknown[] = [];
    const emitter = createEventDispatcher((err) => {
      errors.push(err);
    });
    const received: string[] = [];
    emitter.subscribe(() => {
      throw new Error('boom');
    });
    emitter.subscribe((e) => {
      received.push(e.type);
    });
    emitter.emit({ type: 'tick' as never, monotonicMs: 0, wallIso: '' });
    expect(errors).toHaveLength(1);
    expect(received).toEqual(['tick']);
  });

  it('clear() removes all listeners', () => {
    const emitter = createEventDispatcher();
    emitter.subscribe(() => undefined);
    emitter.subscribe(() => undefined);
    expect(emitter.listenerCount()).toBe(2);
    emitter.clear();
    expect(emitter.listenerCount()).toBe(0);
  });

  it('emit is synchronous (no microtask delay)', () => {
    const emitter = createEventDispatcher();
    let dispatched = false;
    emitter.subscribe(() => {
      dispatched = true;
    });
    emitter.emit({ type: 'started' as never, monotonicMs: 0, wallIso: '' });
    expect(dispatched).toBe(true);
  });

  it('handles zero listeners gracefully', () => {
    const emitter = createEventDispatcher();
    expect(() => {
      emitter.emit({ type: 'started' as never, monotonicMs: 0, wallIso: '' });
    }).not.toThrow();
  });
});
