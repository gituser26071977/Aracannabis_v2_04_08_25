/**
 * fakes — Fake Runtime + Fake Adapter + event builders for tests.
 *
 * Mirrors the proven pattern from
 * `__tests__/core/animation-engine/fakes.ts` and
 * `__tests__/core/runtime/fakes.ts`.
 */

import type { RuntimeEngine } from '@core/runtime';
import type {
  BreathEvent,
  RuntimeEvent,
  RuntimeEventListener,
  RuntimeUnsubscribe,
} from '@core/runtime';
import type { TimerEvent } from '@core/timer-engine';

import type { AudioAdapter } from '../../../src/core/audio-engine';
import type { AudioClip } from '../../../src/core/audio-engine';
import type { AudioLayer } from '../../../src/core/audio-engine';

// ─── Fake Runtime ─────────────────────────────────────────────────

export interface FakeRuntime extends RuntimeEngine {
  emit(event: RuntimeEvent): void;
  listenerCount(): number;
}

export const buildFakeRuntime = (): FakeRuntime => {
  const listeners = new Set<RuntimeEventListener>();
  const fake: Partial<FakeRuntime> = {
    subscribe: ((listener: RuntimeEventListener): RuntimeUnsubscribe => {
      listeners.add(listener);
      return (): void => {
        listeners.delete(listener);
      };
    }) as RuntimeEngine['subscribe'],
    emit: ((event: RuntimeEvent): void => {
      for (const l of Array.from(listeners)) {
        l(event);
      }
    }) as FakeRuntime['emit'],
    listenerCount: (): number => listeners.size,
  };
  return fake as FakeRuntime;
};

// ─── Fake Audio Adapter ───────────────────────────────────────────

export interface FakeAudioAdapter extends AudioAdapter {
  readonly playLog: { layer: AudioLayer; clipId: string }[];
  readonly pauseLog: AudioLayer[];
  readonly resumeLog: AudioLayer[];
  readonly stopLog: AudioLayer[];
  readonly loadLog: AudioClip[];
  readonly layerVolumeLog: { layer: AudioLayer; value: number }[];
  readonly masterVolumeLog: number[];
  disposeCount: number;
}

export const buildFakeAudioAdapter = (): FakeAudioAdapter => {
  const playLog: { layer: AudioLayer; clipId: string }[] = [];
  const pauseLog: AudioLayer[] = [];
  const resumeLog: AudioLayer[] = [];
  const stopLog: AudioLayer[] = [];
  const loadLog: AudioClip[] = [];
  const layerVolumeLog: { layer: AudioLayer; value: number }[] = [];
  const masterVolumeLog: number[] = [];

  const adapter: FakeAudioAdapter = {
    id: 'fake-v1',
    playLog,
    pauseLog,
    resumeLog,
    stopLog,
    loadLog,
    layerVolumeLog,
    masterVolumeLog,
    disposeCount: 0,
    load: async () => ({ ok: true, value: undefined }),
    play: async (layer, clipId) => {
      playLog.push({ layer, clipId });
      return { ok: true, value: undefined };
    },
    pause: async (layer) => {
      pauseLog.push(layer);
      return { ok: true, value: undefined };
    },
    resume: async (layer) => {
      resumeLog.push(layer);
      return { ok: true, value: undefined };
    },
    stop: async (layer) => {
      stopLog.push(layer);
      return { ok: true, value: undefined };
    },
    setLayerVolume: async (layer, value) => {
      layerVolumeLog.push({ layer, value });
      return { ok: true, value: undefined };
    },
    setMasterVolume: async (value) => {
      masterVolumeLog.push(value);
      return { ok: true, value: undefined };
    },
    dispose: async () => {
      adapter.disposeCount += 1;
      return { ok: true, value: undefined };
    },
  };
  return adapter;
};

// ─── Event builders ───────────────────────────────────────────────

export const timerEvent = {
  started: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'timer',
    payload: { type: 'started', monotonicMs } as TimerEvent,
  }),
  paused: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'timer',
    payload: { type: 'paused', monotonicMs } as TimerEvent,
  }),
  resumed: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'timer',
    payload: { type: 'resumed', monotonicMs } as TimerEvent,
  }),
  stopped: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'timer',
    payload: { type: 'stopped', monotonicMs } as TimerEvent,
  }),
};

export const breathEvent = {
  phaseChanged: (
    phase: 'idle' | 'preparing' | 'inhale' | 'hold' | 'exhale' | 'completed',
    monotonicMs = 1000,
  ): RuntimeEvent => ({
    source: 'breath',
    payload: {
      type: 'phase-changed',
      previousPhase: null,
      currentPhase: phase,
      cycleIndex: 0,
      phaseProgress: 0,
      monotonicMs,
    } as BreathEvent,
  }),
  breathStarted: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'breath',
    payload: { type: 'breath-started', totalCycles: 6, totalDurationMs: 84_000, monotonicMs } as BreathEvent,
  }),
  completed: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'breath',
    payload: { type: 'completed', totalCycles: 6, totalElapsedMs: 84_000, monotonicMs } as BreathEvent,
  }),
  cancelled: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'breath',
    payload: {
      type: 'cancelled',
      stateBefore: 'inhaling' as never,
      elapsedAtCancelMs: 30_000,
      cyclesCompleted: 3,
      monotonicMs,
    } as BreathEvent,
  }),
  resumedFromInterrupt: (monotonicMs = 1000): RuntimeEvent => ({
    source: 'breath',
    payload: {
      type: 'resumed-from-interrupt',
      stateBefore: 'inhaling' as never,
      interruptedForMs: 2000,
      resumedPhase: 'inhale',
      resumedCycleIndex: 1,
      monotonicMs,
    } as BreathEvent,
  }),
};