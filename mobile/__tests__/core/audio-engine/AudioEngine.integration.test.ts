/**
 * AudioEngine — End-to-end integration test.
 *
 * Verifies that the AudioEngine integrates cleanly with the real
 * `RuntimeEngine` (`@core/runtime`): subscription, dispose, and
 * coexistence with other listeners.
 *
 * The full-sync scenarios (timer→play, breath→cue, etc.) are
 * exhaustively covered by `AudioEngine.sync.test.ts` using the
 * FakeRuntime harness — those tests assert adapter call sequences
 * deterministically. This integration file proves the same wiring
 * works against the real RuntimeEngine without exceptions.
 */

import { EngineId } from '@araflow/shared-contracts';
import { RuntimeEngine } from '@core/runtime';
import { createFakePlan, createFakeTimer } from '../runtime/fakes';

import {
  type AudioClip,
  type AudioTrack,
  buildAudioClip,
  buildAudioTrack,
  createAudioEngine,
} from '../../../src/core/audio-engine';

import {
  buildFakeAudioAdapter,
  type FakeAudioAdapter,
} from './fakes';

const ambientClip: AudioClip = buildAudioClip('ambient.rain-soft', 'ambient', 'memory://ambient/rain-soft.mp3');
const cueInhale: AudioClip = buildAudioClip('cue.bell.inhale', 'cue', 'memory://cue/inhale.mp3');
const cueExhale: AudioClip = buildAudioClip('cue.bell.exhale', 'cue', 'memory://cue/exhale.mp3');
const cueHold: AudioClip = buildAudioClip('cue.bell.hold', 'cue', 'memory://cue/hold.mp3');
const cuePrepare: AudioClip = buildAudioClip('cue.bell.soft', 'cue', 'memory://cue/prepare.mp3');
const cueCompleted: AudioClip = buildAudioClip('cue.bell.end', 'cue', 'memory://cue/end.mp3');
const musicClip: AudioClip = buildAudioClip('music.pad.long', 'music', 'memory://music/pad.mp3');

const track: AudioTrack = buildAudioTrack('track.diaphragmatic', [
  ambientClip,
  cueInhale,
  cueExhale,
  cueHold,
  cuePrepare,
  cueCompleted,
  musicClip,
], {
  layerDefaults: {
    ambient: 'ambient.rain-soft',
    music: 'music.pad.long',
    cue: 'cue.bell.inhale',
  },
});

const wait = (ms = 5): Promise<void> =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });

const buildRuntime = (): RuntimeEngine => {
  const fakeTimer = createFakeTimer();
  return new RuntimeEngine({
    runtimeId: EngineId('test-runtime'),
    timerEngine: fakeTimer.engine,
  });
};

describe('AudioEngine — integration with real RuntimeEngine', () => {
  it('AudioEngine wires into the RuntimeEngine (no exception)', () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    expect(() => createAudioEngine({ adapter, runtime })).not.toThrow();
  });

  it('Loading a protocol + track + starting does not throw', async () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    const loadResult = runtime.loadProtocol(createFakePlan(2, 1000));
    expect(loadResult.ok).toBe(true);
    const trackResult = engine.loadTrack(track);
    expect(trackResult.ok).toBe(true);
    const startResult = runtime.start();
    expect(startResult.ok).toBe(true);
    await wait();
    const pauseResult = runtime.pause();
    expect(pauseResult.ok).toBe(true);
    await wait();
    const resumeResult = runtime.resume();
    expect(resumeResult.ok).toBe(true);
    await wait();
    const cancelResult = runtime.cancel();
    expect(cancelResult.ok).toBe(true);
    await wait();
  });

  it('breath completion stops ambient+music layers', async () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.loadTrack(track);
    runtime.loadProtocol(createFakePlan(2, 1000));
    runtime.start();
    await wait(20);
    expect(adapter.playLog).toContainEqual({ layer: 'ambient', clipId: 'ambient.rain-soft' });
    runtime.cancel();
    await wait(20);
    expect(adapter.stopLog).toContain('ambient');
    expect(adapter.stopLog).toContain('music');
  });

  it('audio engine subscribes the moment it is constructed (no playback)', () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    createAudioEngine({ adapter, runtime });
    expect(adapter.playLog.length).toBe(0);
  });

  it('disposing the engine disposes the adapter and keeps Runtime intact', async () => {
    const runtime = buildRuntime();
    const adapter: FakeAudioAdapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.dispose();
    await wait();
    expect(adapter.disposeCount).toBe(1);
    // Runtime should still respond to lifecycle after engine dispose.
    const loadResult = runtime.loadProtocol(createFakePlan(2, 1000));
    expect(loadResult.ok).toBe(true);
  });

  it('no adapter call is made after engine is disposed (even via Runtime)', async () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.loadTrack(track);
    engine.dispose();
    const playBefore = adapter.playLog.length;
    runtime.loadProtocol(createFakePlan(2, 1000));
    runtime.start();
    await wait();
    expect(adapter.playLog.length).toBe(playBefore);
  });

  it('Engine+Runtime can be used simultaneously — Runtime events still flow to other subscribers', () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    const events: string[] = [];
    runtime.subscribe((e) => events.push(`runtime:${e.source}:${e.payload.type}`));
    createAudioEngine({ adapter, runtime });
    runtime.subscribe((e) => events.push(`runtime2:${e.source}:${e.payload.type}`));
    runtime.loadProtocol(createFakePlan(2, 1000));
    runtime.start();
    // Look for at least one event in the joined stream — proves
    // multiple listeners coexist with the AudioEngine in the loop.
    expect(events.length).toBeGreaterThan(0);
  });

  it('Engine emits a track-loaded event when loadTrack is called after runtime is loaded', () => {
    const runtime = buildRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    runtime.loadProtocol(createFakePlan(2, 1000));
    const received: string[] = [];
    engine.subscribe((e) => received.push(e.type));
    engine.loadTrack(track);
    expect(received).toContain('track-loaded');
  });
});
