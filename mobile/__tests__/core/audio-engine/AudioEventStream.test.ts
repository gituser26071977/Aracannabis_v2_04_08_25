/**
 * AudioEventStream — typed event dispatcher tests.
 */

import {
  type AudioEvent,
  createAudioEventStream,
  type AudioEventStream,
} from '../../../src/core/audio-engine';

describe('AudioEventStream — subscribe / emit', () => {
  it('subscribes a listener that receives events', () => {
    const stream: AudioEventStream = createAudioEventStream();
    const received: AudioEvent[] = [];
    stream.subscribe((e) => received.push(e));
    stream.emit({
      type: 'audio-started',
      trackId: 't1',
      layer: null,
      monotonicMs: 1000,
    });
    expect(received.length).toBe(1);
  });

  it('multiple subscribers each receive the event', () => {
    const stream = createAudioEventStream();
    const a: AudioEvent[] = [];
    const b: AudioEvent[] = [];
    stream.subscribe((e) => a.push(e));
    stream.subscribe((e) => b.push(e));
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(a.length).toBe(1);
    expect(b.length).toBe(1);
  });

  it('unsubscribe stops delivery', () => {
    const stream = createAudioEventStream();
    const received: AudioEvent[] = [];
    const unsubscribe = stream.subscribe((e) => received.push(e));
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(received.length).toBe(1);
    unsubscribe();
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(received.length).toBe(1);
  });

  it('re-entrant subscribe during emit is safe (snapshot semantics)', () => {
    const stream = createAudioEventStream();
    const added: string[] = [];
    stream.subscribe(() => {
      stream.subscribe((e) => added.push(`late:${e.type}`));
    });
    stream.emit({ type: 'audio-started', trackId: 't', layer: null, monotonicMs: 0 });
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(added).toContain('late:audio-stopped');
  });

  it('listener errors do not break other listeners', () => {
    const errors: unknown[] = [];
    const stream = createAudioEventStream((err) => errors.push(err));
    let secondCalled = false;
    stream.subscribe(() => {
      throw new Error('boom');
    });
    stream.subscribe(() => {
      secondCalled = true;
    });
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(errors.length).toBe(1);
    expect(secondCalled).toBe(true);
  });

  it('listener errors silently pass when no onListenerError sink', () => {
    const stream = createAudioEventStream();
    let secondCalled = false;
    stream.subscribe(() => {
      throw new Error('silent boom');
    });
    stream.subscribe(() => {
      secondCalled = true;
    });
    stream.emit({ type: 'audio-started', trackId: 't', layer: null, monotonicMs: 0 });
    expect(secondCalled).toBe(true);
  });

  it('clear removes all listeners', () => {
    const stream = createAudioEventStream();
    const received: AudioEvent[] = [];
    stream.subscribe((e) => received.push(e));
    stream.clear();
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    expect(received.length).toBe(0);
  });

  it('listenerCount reflects subscriptions and unsubscriptions', () => {
    const stream = createAudioEventStream();
    expect(stream.listenerCount()).toBe(0);
    const u1 = stream.subscribe(() => undefined);
    expect(stream.listenerCount()).toBe(1);
    const u2 = stream.subscribe(() => undefined);
    expect(stream.listenerCount()).toBe(2);
    u1();
    expect(stream.listenerCount()).toBe(1);
    u2();
    expect(stream.listenerCount()).toBe(0);
  });

  it('emitting 11 different event types works', () => {
    const stream = createAudioEventStream();
    const received: AudioEvent[] = [];
    stream.subscribe((e) => received.push(e));
    stream.emit({ type: 'audio-started', trackId: 't', layer: null, monotonicMs: 0 });
    stream.emit({ type: 'audio-paused', atElapsedMs: 0, monotonicMs: 0 });
    stream.emit({ type: 'audio-resumed', pausedForMs: 0, monotonicMs: 0 });
    stream.emit({ type: 'audio-stopped', reason: 'completed', monotonicMs: 0 });
    stream.emit({ type: 'track-loaded', trackId: 't', layer: 'guidance', clipCount: 1, monotonicMs: 0 });
    stream.emit({ type: 'cue-played', cueId: 'c', layer: 'cue', monotonicMs: 0 });
    stream.emit({ type: 'guidance-played', text: 'Inspire', language: 'pt-BR', monotonicMs: 0 });
    stream.emit({ type: 'ambient-started', trackId: 't', monotonicMs: 0 });
    stream.emit({ type: 'music-started', trackId: 't', monotonicMs: 0 });
    stream.emit({ type: 'volume-changed', layer: 'master', value: 0.5, monotonicMs: 0 });
    stream.emit({ type: 'mute-changed', muted: true, monotonicMs: 0 });
    expect(received.length).toBe(11);
  });
});
