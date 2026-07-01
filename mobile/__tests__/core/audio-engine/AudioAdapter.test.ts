/**
 * InMemoryAudioAdapter — unit tests.
 *
 * Asserts every method records into the right log, dispose is
 * idempotent, and `failAfterDispose` semantics work.
 */

import {
  buildAudioClip,
  createInMemoryAudioAdapter,
  InMemoryAudioAdapter,
} from '../../../src/core/audio-engine';

const clip = buildAudioClip('cue.test', 'cue', 'memory://cue/test.mp3');

describe('InMemoryAudioAdapter — construction', () => {
  it('has stable id and empty logs initially', () => {
    const adapter = createInMemoryAudioAdapter();
    expect(adapter.id).toBe('in-memory-v1');
    expect(adapter.snapshot().playCount).toBe(0);
    expect(adapter.disposed).toBe(false);
  });
});

describe('InMemoryAudioAdapter — load', () => {
  it('records load and returns ok', async () => {
    const adapter = createInMemoryAudioAdapter();
    const result = await adapter.load(clip);
    expect(result.ok).toBe(true);
    expect(adapter.loadLog).toContain(clip);
    expect(adapter.snapshot().loadCount).toBe(1);
  });
});

describe('InMemoryAudioAdapter — play / pause / resume / stop', () => {
  it('play records layer+clipId', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.play('cue', 'cue.bell.inhale');
    expect(adapter.playLog).toEqual([{ layer: 'cue', clipId: 'cue.bell.inhale' }]);
  });

  it('pause records layer', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.pause('guidance');
    expect(adapter.pauseLog).toEqual(['guidance']);
  });

  it('resume records layer', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.resume('ambient');
    expect(adapter.resumeLog).toEqual(['ambient']);
  });

  it('stop records layer', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.stop('music');
    expect(adapter.stopLog).toEqual(['music']);
  });

  it('multiple calls accumulate in logs', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.play('cue', 'a');
    await adapter.play('cue', 'b');
    await adapter.pause('cue');
    await adapter.resume('cue');
    await adapter.stop('cue');
    expect(adapter.playLog.length).toBe(2);
    expect(adapter.pauseLog.length).toBe(1);
    expect(adapter.resumeLog.length).toBe(1);
    expect(adapter.stopLog.length).toBe(1);
  });
});

describe('InMemoryAudioAdapter — volume', () => {
  it('setLayerVolume records value', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.setLayerVolume('guidance', 0.5);
    expect(adapter.layerVolumeLog).toEqual([{ layer: 'guidance', value: 0.5 }]);
  });

  it('setMasterVolume records value', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.setMasterVolume(0.7);
    expect(adapter.masterVolumeLog).toEqual([0.7]);
  });

  it('snapshot accumulates across all volume calls', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.setLayerVolume('guidance', 0.5);
    await adapter.setLayerVolume('cue', 0.6);
    await adapter.setMasterVolume(0.8);
    const s = adapter.snapshot();
    expect(s.setLayerVolumeCount).toBe(2);
    expect(s.setMasterVolumeCount).toBe(1);
  });
});

describe('InMemoryAudioAdapter — dispose', () => {
  it('first dispose increments counter and flips flag', async () => {
    const adapter = createInMemoryAudioAdapter();
    const r1 = await adapter.dispose();
    expect(r1.ok).toBe(true);
    expect(adapter.disposed).toBe(true);
    expect(adapter.disposeCount).toBe(1);
  });

  it('subsequent disposes are idempotent (default option)', async () => {
    const adapter = createInMemoryAudioAdapter();
    await adapter.dispose();
    const r2 = await adapter.dispose();
    expect(r2.ok).toBe(true);
    expect(adapter.disposeCount).toBe(2);
  });

  it('with failAfterDispose, all methods after dispose return Err', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    await adapter.dispose();
    const r = await adapter.play('cue', 'cue.x');
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error.code).toBe('audio_adapter_disposed');
    }
  });

  it('with failAfterDispose, multiple post-dispose calls all fail', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    await adapter.dispose();
    const r1 = await adapter.pause('guidance');
    const r2 = await adapter.resume('ambient');
    const r3 = await adapter.stop('music');
    expect(r1.ok).toBe(false);
    expect(r2.ok).toBe(false);
    expect(r3.ok).toBe(false);
  });

  it('with failAfterDispose, load returns Err after dispose', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    await adapter.dispose();
    const r = await adapter.load(clip);
    expect(r.ok).toBe(false);
  });

  it('with failAfterDispose, setLayerVolume returns Err after dispose', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    await adapter.dispose();
    const r = await adapter.setLayerVolume('guidance', 0.5);
    expect(r.ok).toBe(false);
  });

  it('with failAfterDispose, setMasterVolume returns Err after dispose', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    await adapter.dispose();
    const r = await adapter.setMasterVolume(0.7);
    expect(r.ok).toBe(false);
  });

  it('dispose always returns ok', async () => {
    const adapter = createInMemoryAudioAdapter({ failAfterDispose: true });
    const r = await adapter.dispose();
    expect(r.ok).toBe(true);
  });
});

describe('InMemoryAudioAdapter — simulated latency', () => {
  it('resolves after simulatedLatencyMs', async () => {
    const adapter = createInMemoryAudioAdapter({ simulatedLatencyMs: 30 });
    const t0 = Date.now();
    await adapter.play('cue', 'cue.x');
    const elapsed = Date.now() - t0;
    expect(elapsed).toBeGreaterThanOrEqual(25);
  });
});

describe('InMemoryAudioAdapter — class export', () => {
  it('InMemoryAudioAdapter is the same class as createInMemoryAudioAdapter returns', () => {
    const adapter = createInMemoryAudioAdapter();
    expect(adapter).toBeInstanceOf(InMemoryAudioAdapter);
  });
});
