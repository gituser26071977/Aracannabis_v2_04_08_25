/**
 * fakes — controlled substitutes for the real Core engines,
 * used by RuntimeEngine unit tests.
 *
 * - `createFakeTimer` — TimerEngine double. Implements the structural
 *   shape with `start/stop/subscribe/getTotalElapsedMs/getState/snapshot/
 *   notifyBackground/notifyForeground` and a manually-advanceable clock.
 *
 * - `createFakePlan` — minimal valid ProtocolExecutionPlan with N phases
 *   and configurable duration, for tests that don't need full compiler.
 *
 * - `captureEvents` — returns a listener + the captured events array.
 */

import {
  EngineId,
  type BreathPhase,
  type CurveType,
  Duration,
  type Failure,
  ProtocolId,
} from '@araflow/shared-contracts';

import {
  buildExecutionPlan,
  type PlanPhaseStep,
  type ProtocolExecutionPlan,
} from '@core/protocol-compiler';
import type { TimerEngine } from '@core/timer-engine';

import type { RuntimeEvent } from '../../../src/core/runtime';

export interface FakeTimerControls {
  readonly engine: TimerEngine;
  advance(ms: number): void;
  emitTick(monotonicMs: number, elapsedMs: number): void;
  setState(s: 'idle' | 'running' | 'paused' | 'stopped'): void;
}

export const createFakeTimer = (): FakeTimerControls => {
  type Listener = (event: { type: string; monotonicMs: number; [k: string]: unknown }) => void;
  const listeners = new Set<Listener>();
  let elapsedMs = 0;
  let state: 'idle' | 'running' | 'paused' | 'stopped' = 'idle';

  const engine = {
    start: (): void => {
      state = 'running';
    },
    stop: (): void => {
      state = 'stopped';
    },
    pause: (): void => {
      state = 'paused';
    },
    resume: (): void => {
      state = 'running';
    },
    reset: (): void => {
      elapsedMs = 0;
      state = 'idle';
    },
    subscribe: (listener: Listener): (() => void) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getTotalElapsedMs: (): number => elapsedMs,
    getState: (): 'idle' | 'running' | 'paused' | 'stopped' => state,
    getMode: () => 'balanced' as const,
    getTimeScale: (): number => 1,
    getTickIntervalMs: (): number => 100,
    getTotalPausedMs: (): number => 0,
    getTotalBackgroundedMs: (): number => 0,
    getTickIndex: (): number => Math.floor(elapsedMs / 100),
    getSessionStartedAtWallIso: (): string => new Date(0).toISOString(),
    snapshot: () => ({
      state,
      mode: 'balanced' as const,
      timeScale: 1,
      tickIntervalMs: 100,
      totalElapsedMs: elapsedMs,
      totalActiveMs: elapsedMs,
      totalPausedMs: 0,
      totalBackgroundedMs: 0,
      tickIndex: Math.floor(elapsedMs / 100),
      listenerCount: listeners.size,
    }),
    notifyBackground: (): void => {
      // no-op
    },
    notifyForeground: (): void => {
      // no-op
    },
    setMode: (): void => {
      // no-op
    },
    setTimeScale: (): void => {
      // no-op
    },
  } as unknown as TimerEngine;

  const advance = (ms: number): void => {
    elapsedMs += ms;
  };

  const emitTick = (monotonicMs: number, _el: number): void => {
    for (const listener of [...listeners]) {
      listener({ type: 'tick', monotonicMs });
    }
  };

  const setState = (s: 'idle' | 'running' | 'paused' | 'stopped'): void => {
    state = s;
  };

  return { engine, advance, emitTick, setState };
};

export const captureEvents = (): {
  events: RuntimeEvent[];
  listener: (e: RuntimeEvent) => void;
} => {
  const events: RuntimeEvent[] = [];
  const listener = (e: RuntimeEvent): void => {
    events.push(e);
  };
  return { events, listener };
};

export const createFakePlan = (
  cycles: number,
  phaseDurationMs: number,
  protocolIdStr = '01ARZ3NDEKTSV4RRFFQ69G5FAV',
): ProtocolExecutionPlan => {
  const phase: BreathPhase = 'inhaling';
  const curve: CurveType = 'easeInOut';
  const steps: PlanPhaseStep[] = [];
  for (let i = 0; i < cycles; i += 1) {
    steps.push({
      index: i,
      phase,
      duration: Duration(phaseDurationMs),
      curve,
    });
  }
  const compiledBy = EngineId('test-compiler');
  const phaseDurationNum = phaseDurationMs;
  return buildExecutionPlan({
    executionId: '01HXYZTESTEXECUTIONID00000000',
    protocolId: ProtocolId(protocolIdStr),
    version: '1.0.0',
    schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
    compilerVersion: '1.0.0',
    title: 'fake',
    metadata: {
      author: 'test',
      references: [],
      language: 'en',
      evidenceLevel: 'C',
      contraindications: [],
      category: 'test',
      tags: [],
      approvedAt: new Date(0).toISOString(),
    },
    phases: steps,
    cycles,
    totalCycleDuration: Duration(phaseDurationNum),
    totalDuration: Duration(phaseDurationNum * cycles),
    checksum: '0x0000000000000000',
    compiledAt: new Date(0).toISOString(),
    compiledBy,
  }) as ProtocolExecutionPlan;
};

export const silentWarnings: readonly Failure[] = [];
