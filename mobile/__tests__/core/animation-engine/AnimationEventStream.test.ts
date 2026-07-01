/**
 * Tests for AnimationEventStream — listener isolation, snapshot
 * semantics, re-entrant subscribe/unsubscribe, and error sink.
 */

import { createAnimationEventStream } from '@core/animation-engine';

describe('AnimationEventStream — basic', () => {
  it('size reflects subscription count', () => {
    const stream = createAnimationEventStream();
    expect(stream.size()).toBe(0);
    const off = stream.subscribe(() => undefined);
    expect(stream.size()).toBe(1);
    off();
    expect(stream.size()).toBe(0);
  });

  it('subscribe returns a working unsubscribe', () => {
    const stream = createAnimationEventStream();
    const received: unknown[] = [];
    const off = stream.subscribe((e) => received.push(e));
    stream.emit({ type: 'animation-engine-started', monotonicMs: 1 }, () => undefined);
    expect(received.length).toBe(1);
    off();
    stream.emit({ type: 'animation-engine-started', monotonicMs: 2 }, () => undefined);
    expect(received.length).toBe(1);
  });

  it('clear empties the listener set', () => {
    const stream = createAnimationEventStream();
    stream.subscribe(() => undefined);
    stream.subscribe(() => undefined);
    expect(stream.size()).toBe(2);
    stream.clear();
    expect(stream.size()).toBe(0);
  });
});

describe('AnimationEventStream — listener isolation', () => {
  it('routes a throwing listener to onError', () => {
    const stream = createAnimationEventStream();
    const errors: unknown[] = [];
    stream.subscribe(() => {
      throw new Error('boom');
    });
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, (e) =>
      errors.push(e),
    );
    expect(errors.length).toBe(1);
  });

  it('keeps emitting to other listeners after a throw', () => {
    const stream = createAnimationEventStream();
    let ok = 0;
    stream.subscribe(() => {
      throw new Error('boom');
    });
    stream.subscribe(() => {
      ok += 1;
    });
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => undefined);
    expect(ok).toBe(1);
  });

  it('swallows errors thrown by the error sink itself', () => {
    const stream = createAnimationEventStream();
    stream.subscribe(() => {
      throw new Error('boom');
    });
    expect(() =>
      stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => {
        throw new Error('sink boom');
      }),
    ).not.toThrow();
  });
});

describe('AnimationEventStream — re-entrant subscribe', () => {
  it('a listener subscribed during emit does not receive the current event', () => {
    const stream = createAnimationEventStream();
    let early = 0;
    let late = 0;
    stream.subscribe(() => {
      early += 1;
      stream.subscribe(() => {
        late += 1;
      });
    });
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => undefined);
    expect(early).toBe(1);
    expect(late).toBe(0);
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => undefined);
    expect(late).toBe(1);
  });

  it('a listener unsubscribed during emit does not receive subsequent events', () => {
    const stream = createAnimationEventStream();
    let count = 0;
    const off = stream.subscribe(() => {
      count += 1;
      off();
    });
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => undefined);
    expect(count).toBe(1);
    stream.emit({ type: 'animation-frame', monotonicMs: 0, frame: {} as never }, () => undefined);
    expect(count).toBe(1);
  });
});
