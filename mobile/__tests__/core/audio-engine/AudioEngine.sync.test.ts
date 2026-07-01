/**
 * AudioEngine — Runtime sync tests.
 *
 * Asserts that the Audio Engine reacts to each Runtime event correctly
 * via adapter.play/pause/resume/stop.
 */

import {
  type AudioClip,
  type AudioEvent,
  type AudioTrack,
  buildAudioClip,
  buildAudioTrack,
  createAudioEngine,
} from '../../../src/core/audio-engine';

import {
  breathEvent,
  buildFakeAudioAdapter,
  buildFakeRuntime,
  timerEvent,
  type FakeAudioAdapter,
  type FakeRuntime,
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

// Tiny wait helper for micro-tasks flushed by async adapter calls.
const wait = (ms = 1): Promise<void> =>
  new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });

const setupEngine = (): { engine: ReturnType<typeof createAudioEngine>; runtime: FakeRuntime; adapter: FakeAudioAdapter } => {
  const runtime = buildFakeRuntime();
  const adapter = buildFakeAudioAdapter();
  const engine = createAudioEngine({ adapter, runtime });
  engine.loadTrack(track);
  return { engine, runtime, adapter };
};

describe('AudioEngine — timer sync', () => {
  it('timer.started → audio play()', () => {
    const { engine, runtime, adapter } = setupEngine();
    runtime.emit(timerEvent.started());
    expect(engine.getState()).toBe('playing');
    expect(adapter.playLog.some((p) => p.layer === 'cue')).toBe(false);
  });

  it('timer.paused → audio pause()', () => {
    const { engine, runtime } = setupEngine();
    runtime.emit(timerEvent.started());
    runtime.emit(timerEvent.paused());
    expect(engine.getState()).toBe('paused');
  });

  it('timer.resumed → audio resume()', () => {
    const { engine, runtime } = setupEngine();
    runtime.emit(timerEvent.started());
    runtime.emit(timerEvent.paused());
    runtime.emit(timerEvent.resumed());
    expect(engine.getState()).toBe('playing');
  });

  it('timer.stopped → audio stop()', () => {
    const { engine, runtime, adapter } = setupEngine();
    runtime.emit(timerEvent.started());
    runtime.emit(timerEvent.stopped());
    expect(engine.getState()).toBe('stopped');
    expect(adapter.stopLog).toContain('guidance');
    expect(adapter.stopLog).toContain('cue');
    expect(adapter.stopLog).toContain('ambient');
    expect(adapter.stopLog).toContain('music');
  });
});

describe('AudioEngine — Runtime sync ignores when disposed', () => {
  it('events after dispose do not call adapter', async () => {
    const runtime = buildFakeRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.loadTrack(track);
    engine.dispose();
    const before = adapter.playLog.length;
    runtime.emit(breathEvent.phaseChanged('inhale'));
    expect(adapter.playLog.length).toBe(before);
  });

  it('timer events after dispose are ignored', () => {
    const runtime = buildFakeRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.dispose();
    const before = adapter.pauseLog.length;
    runtime.emit(timerEvent.paused());
    expect(adapter.pauseLog.length).toBe(before);
  });
});

describe('AudioEngine — Runtime event defaults', () => {
  it('unknown timer payload type is ignored', () => {
    const runtime = buildFakeRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    engine.loadTrack(track);
    const before = adapter.playLog.length;
    runtime.emit({ source: 'timer', payload: { type: 'unknown-type', monotonicMs: 0 } as never });
    expect(adapter.playLog.length).toBe(before);
    expect(engine.getState()).toBe('loaded');
  });
});

describe('AudioEngine — breath.phase-changed → cue + guidance', () => {
  it('inhale phase → cue.bell.inhale + guidance PT', () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(breathEvent.phaseChanged('inhale'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.inhale' });
    expect(adapter.playLog).toContainEqual({ layer: 'guidance', clipId: 'guidance.pt-BR.inhale' });
  });

  it('exhale phase → cue.bell.exhale + guidance PT', () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(breathEvent.phaseChanged('exhale'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.exhale' });
    expect(adapter.playLog).toContainEqual({ layer: 'guidance', clipId: 'guidance.pt-BR.exhale' });
  });

  it('hold phase → cue.bell.hold + guidance PT', () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(breathEvent.phaseChanged('hold'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.hold' });
  });

  it('preparing phase → cue.bell.soft + guidance PT', () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(breathEvent.phaseChanged('preparing'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.soft' });
  });

  it('completed phase → cue.bell.end', () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(breathEvent.phaseChanged('completed'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.end' });
  });

  it('idle phase → no cue', () => {
    const { runtime, adapter } = setupEngine();
    const before = adapter.playLog.length;
    runtime.emit(breathEvent.phaseChanged('idle'));
    expect(adapter.playLog.length).toBe(before);
  });

  it('English language → uses en-US cue ids and guidance', () => {
    const { engine, runtime, adapter } = setupEngine();
    engine.setLanguage('en-US');
    runtime.emit(breathEvent.phaseChanged('inhale'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.inhale' });
    expect(adapter.playLog).toContainEqual({ layer: 'guidance', clipId: 'guidance.en-US.inhale' });
  });
});

describe('AudioEngine — breath.breath-started → ambient + music', () => {
  it('starts ambient and music when breath begins', async () => {
    const { runtime, adapter } = setupEngine();
    // Engine must be playing first (timer.started).
    runtime.emit(timerEvent.started());
    await wait(1);
    runtime.emit(breathEvent.breathStarted(1000));
    await wait(1);
    expect(adapter.playLog).toContainEqual({ layer: 'ambient', clipId: 'ambient.rain-soft' });
    expect(adapter.playLog).toContainEqual({ layer: 'music', clipId: 'music.pad.long' });
  });

  it('emits ambient-started and music-started events', async () => {
    const { engine, runtime } = setupEngine();
    const events: AudioEvent[] = [];
    engine.subscribe((e) => events.push(e));
    runtime.emit(timerEvent.started());
    await wait(1);
    runtime.emit(breathEvent.breathStarted(2000));
    await wait(1);
    const types = new Set(events.map((e) => e.type));
    expect(types.has('ambient-started')).toBe(true);
    expect(types.has('music-started')).toBe(true);
  });
});

describe('AudioEngine — breath.completed / breath.cancelled → stop ambient+music', () => {
  it('completed → stops ambient and music', async () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(timerEvent.started());
    await wait(1);
    runtime.emit(breathEvent.breathStarted(1000));
    await wait(1);
    runtime.emit(breathEvent.completed(5000));
    await wait(1);
    expect(adapter.stopLog).toContain('ambient');
    expect(adapter.stopLog).toContain('music');
  });

  it('cancelled → stops ambient and music', async () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(timerEvent.started());
    await wait(1);
    runtime.emit(breathEvent.breathStarted(1000));
    await wait(1);
    runtime.emit(breathEvent.cancelled(3000));
    await wait(1);
    expect(adapter.stopLog).toContain('ambient');
    expect(adapter.stopLog).toContain('music');
  });
});

describe('AudioEngine — breath.resumed-from-interrupt → resume all layers', () => {
  it('resumes guidance, cue, ambient, music', async () => {
    const { runtime, adapter } = setupEngine();
    runtime.emit(timerEvent.started());
    await wait(1);
    runtime.emit(breathEvent.breathStarted(1000));
    await wait(1);
    runtime.emit(breathEvent.resumedFromInterrupt(4000));
    await wait(1);
    expect(adapter.resumeLog).toContain('guidance');
    expect(adapter.resumeLog).toContain('cue');
    expect(adapter.resumeLog).toContain('ambient');
    expect(adapter.resumeLog).toContain('music');
  });
});

describe('AudioEngine — phase-changed works without track loaded', () => {
  it('phase-changed cue mapping works before loadTrack (cue table is independent)', () => {
    const runtime = buildFakeRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    // No loadTrack — phase events still resolve cue ids (cue table is
    // pure and track-independent), but ambient/music layers do not start.
    runtime.emit(breathEvent.phaseChanged('inhale'));
    expect(adapter.playLog).toContainEqual({ layer: 'cue', clipId: 'cue.bell.inhale' });
    expect(adapter.playLog).toContainEqual({ layer: 'guidance', clipId: 'guidance.pt-BR.inhale' });
    expect(engine.getActiveTrack()).toBeNull();
  });

  it('breath-started before loadTrack does not start ambient/music', () => {
    const runtime = buildFakeRuntime();
    const adapter = buildFakeAudioAdapter();
    const engine = createAudioEngine({ adapter, runtime });
    runtime.emit(timerEvent.started());
    runtime.emit(breathEvent.breathStarted(1000));
    expect(adapter.playLog.some((p) => p.layer === 'ambient')).toBe(false);
    expect(adapter.playLog.some((p) => p.layer === 'music')).toBe(false);
  });
});
