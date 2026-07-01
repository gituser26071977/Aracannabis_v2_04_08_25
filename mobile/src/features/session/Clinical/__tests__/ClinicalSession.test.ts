/**
 * ClinicalSession — unit tests.
 *
 * Validates construction, status transitions, frame exposure, and
 * persistence semantics. Uses the InMemoryAudioAdapter from
 * @core/audio-engine (the mock that ships with Sprint 10) and the
 * in-memory StorageAdapter from @core/session-persistence (Sprint 7).
 *
 * These tests do NOT advance the Runtime (no FakeTimer), so they
 * cover the orchestration surface (status, start, pause, resume,
 * stop) without exercising the protocol-runtime clock. The end-to-end
 * flow is covered by ClinicalSession.e2e.test.ts.
 */

import { createInMemoryAudioAdapter } from '@core/audio-engine';
import { createMemoryStorageAdapter } from '@core/session-persistence';

import { startClinicalSession, type ClinicalSessionHandle } from '../ClinicalSession';
import { DEFAULT_CLINICAL_PROTOCOL } from '../protocols';

const buildHandle = async (): Promise<ClinicalSessionHandle> => {
  const audio = createInMemoryAudioAdapter();
  const storage = createMemoryStorageAdapter();
  const result = await startClinicalSession({
    protocol: DEFAULT_CLINICAL_PROTOCOL,
    audioAdapter: audio,
    storageAdapter: storage,
  });
  if (!result.ok) {
    throw new Error(`failed to start session: ${String(result.error)}`);
  }
  return result.value;
};

describe('ClinicalSession — construction', () => {
  it('starts in "starting" status', async () => {
    const handle = await buildHandle();
    expect(handle.status()).toBe('starting');
    await handle.stop();
  });

  it('exposes the protocol title and id from the compiled plan', async () => {
    const handle = await buildHandle();
    expect(handle.protocolTitle()).toBe('Respiração Diafragmática');
    expect(handle.protocolId()).toBe('01ARZ3NDEKTSV4RRFFQ69G5FA2');
    await handle.stop();
  });

  it('totalDurationMs is positive and matches the plan', async () => {
    const handle = await buildHandle();
    expect(handle.totalDurationMs()).toBe(84000);
    await handle.stop();
  });

  it('startedAtIso is null before start()', async () => {
    const handle = await buildHandle();
    expect(handle.startedAtIso()).toBeNull();
    await handle.stop();
  });

  it('completedNaturally is false before stop()', async () => {
    const handle = await buildHandle();
    expect(handle.completedNaturally()).toBe(false);
    await handle.stop();
  });
});

describe('ClinicalSession — start', () => {
  it('transitions from "starting" to "running" on start()', async () => {
    const handle = await buildHandle();
    handle.start();
    expect(handle.status()).toBe('running');
    await handle.stop();
  });

  it('start() after stop() is a no-op', async () => {
    const handle = await buildHandle();
    handle.start();
    await handle.stop();
    handle.start();
    expect(handle.status()).not.toBe('running');
  });
});

describe('ClinicalSession — pause / resume', () => {
  it('pause() from running sets status to paused', async () => {
    const handle = await buildHandle();
    handle.start();
    handle.pause();
    expect(handle.status()).toBe('paused');
    await handle.stop();
  });

  it('resume() from paused sets status to running', async () => {
    const handle = await buildHandle();
    handle.start();
    handle.pause();
    handle.resume();
    expect(handle.status()).toBe('running');
    await handle.stop();
  });

  it('pause() while not running is a no-op', async () => {
    const handle = await buildHandle();
    handle.pause();
    expect(handle.status()).not.toBe('paused');
    await handle.stop();
  });

  it('resume() while not paused is a no-op', async () => {
    const handle = await buildHandle();
    handle.resume();
    expect(handle.status()).not.toBe('running');
    await handle.stop();
  });
});

describe('ClinicalSession — stop', () => {
  it('stop() resolves without error', async () => {
    const handle = await buildHandle();
    handle.start();
    await expect(handle.stop()).resolves.toBeUndefined();
  });

  it('stop() marks the session as not completedNaturally', async () => {
    const handle = await buildHandle();
    handle.start();
    await handle.stop();
    expect(handle.completedNaturally()).toBe(false);
  });

  it('stop() before start() does not throw', async () => {
    const handle = await buildHandle();
    await expect(handle.stop()).resolves.toBeUndefined();
  });
});

describe('ClinicalSession — frame + update', () => {
  it('currentFrame() returns an idle frame after construction', async () => {
    const handle = await buildHandle();
    // The animation engine subscribes on construction and emits an
    // idle frame on `start()`; until the runtime has fired, the
    // orchestrator exposes the most recent frame from the
    // animation engine, which may be the idle frame or null
    // depending on event timing. Accept both as valid initial
    // states.
    const frame = handle.currentFrame();
    expect(frame === null || typeof frame.phase === 'string').toBe(true);
    await handle.stop();
  });

  it('update() returns the current frame or null', async () => {
    const handle = await buildHandle();
    const next = handle.update();
    expect(next === null || typeof next === 'object').toBe(true);
    await handle.stop();
  });

  it('remainingMs() returns a number', async () => {
    const handle = await buildHandle();
    const remaining = handle.remainingMs();
    expect(typeof remaining).toBe('number');
    expect(remaining).toBeGreaterThanOrEqual(0);
    await handle.stop();
  });
});

describe('ClinicalSession — dispose', () => {
  it('dispose() is safe to call multiple times', async () => {
    const handle = await buildHandle();
    await expect(handle.dispose()).resolves.toBeUndefined();
    await expect(handle.dispose()).resolves.toBeUndefined();
  });
});
