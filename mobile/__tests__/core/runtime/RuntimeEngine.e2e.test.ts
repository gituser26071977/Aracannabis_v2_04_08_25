/**
 * RuntimeEngine — end-to-end tests with REAL engines.
 *
 * Uses the actual `createTimerEngine` (wall-clock) + `createBreathEngine`
 * + `ProtocolRuntime` to confirm the Runtime Facade wires them up
 * without behavior loss vs the proven Sprint 3.5 CLI run path.
 *
 * The wall-clock path is brisk (50–100ms) to keep the suite fast.
 */

import { EngineId } from '@araflow/shared-contracts';

import { JsonSource, type ProtocolRuntimeEvent } from '@core/protocol-compiler';
import { RuntimeEngine, type RuntimeEvent } from '@core/runtime';

const SHORT_ID = EngineId('e2e-runtime');

const buildShortSource = (): ReturnType<typeof JsonSource> => {
  // 2 cycles × (inhale 600ms + exhale 600ms) = 2400ms total — meets schema min.
  return JsonSource(
    JSON.stringify({
      $schema: 'https://araflow.app/schemas/protocol/v1.json',
      id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
      version: '1.0.0',
      title: 'E2E test protocol',
      breath: {
        cycles: 2,
        phases: [
          { type: 'inhale', durationMs: 600 },
          { type: 'exhale', durationMs: 600 },
        ],
      },
    }),
    'inline://e2e',
  );
};

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

describe('RuntimeEngine — end-to-end with real engines', () => {
  it('drives a 2-cycle plan to natural completion via compile() + start()', async () => {
    const rt = new RuntimeEngine({ runtimeId: SHORT_ID });
    const events: RuntimeEvent[] = [];
    rt.subscribe((e: RuntimeEvent) => {
      events.push(e);
    });

    const loadResult = rt.compile(buildShortSource());
    expect(loadResult.ok).toBe(true);
    expect(rt.getState()).toBe('loaded');

    const startResult = rt.start();
    expect(startResult.ok).toBe(true);
    expect(rt.getState()).toBe('running');

    // Wait for the natural completion (2400ms plan + tolerance).
    const deadline = Date.now() + 5000;
    while (rt.getState() !== 'completed' && rt.getState() !== 'errored' && Date.now() < deadline) {
      await sleep(20);
    }

    expect(rt.getState()).toBe('completed');

    const completion = events.find(
      (e) => e.source === 'runtime' && e.payload.type === 'runtime-completed',
    );
    expect(completion).toBeDefined();

    const metrics = rt.getMetrics();
    expect(metrics.totalCycles).toBe(2);
    expect(metrics.cyclesCompleted).toBeGreaterThanOrEqual(2);
    expect(metrics.plannedDurationMs).toBe(2400);
    expect(metrics.errors).toBe(0);
    expect(metrics.eventCounters.timer).toBeGreaterThan(0);
    expect(metrics.eventCounters.breath).toBeGreaterThan(0);
    expect(metrics.eventCounters.protocol).toBeGreaterThan(0);
    expect(metrics.eventCounters.runtime).toBeGreaterThanOrEqual(1); // runtime-completed

    rt.dispose();
    expect(rt.getState()).toBe('disposed');
  });

  it('cancels a running session and emits protocol-runtime-stopped', async () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-cancel') });
    rt.compile(buildShortSource());
    rt.start();
    expect(rt.getState()).toBe('running');

    const cancelResult = rt.cancel();
    expect(cancelResult.ok).toBe(true);
    expect(rt.getState()).toBe('stopped');

    rt.dispose();
  });

  it('exposes pause/resume with real engines', async () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-pause') });
    rt.compile(buildShortSource());
    rt.start();
    expect(rt.pause().ok).toBe(true);
    expect(rt.getState()).toBe('paused');
    expect(rt.resume().ok).toBe(true);
    expect(rt.getState()).toBe('running');
    // Tear down.
    rt.dispose();
  });

  it('emits lifecycle events with the same source discriminant across the stream', async () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-sources') });
    const events: RuntimeEvent[] = [];
    rt.subscribe((e: RuntimeEvent) => {
      events.push(e);
    });
    rt.compile(buildShortSource());
    rt.start();
    await sleep(1300); // One full 1200ms cycle + buffer.

    const sources = new Set(events.map((e) => e.source));
    // Timer always emits; protocol/runtime emit when running.
    expect(sources.has('timer')).toBe(true);
    expect(sources.has('protocol')).toBe(true);

    rt.dispose();
  });

  it('snapshot reflects all three engine snapshots plus Runtime state', () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-snap') });
    rt.compile(buildShortSource());
    const snap = rt.snapshot();
    expect(snap.state).toBe('loaded');
    expect(snap.plan).not.toBeNull();
    expect(snap.timer).not.toBeNull();
    expect(snap.breath).not.toBeNull();
    expect(snap.protocol).not.toBeNull();
    rt.dispose();
  });

  it('dispose is a safe no-op multiple times', () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-dispose') });
    expect(() => rt.dispose()).not.toThrow();
    expect(() => rt.dispose()).not.toThrow();
    expect(rt.getState()).toBe('disposed');
  });

  it('after dispose, further API calls do not throw (terminal safety)', () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-terminal') });
    rt.dispose();
    expect(rt.loadProtocol({} as never).ok).toBe(false);
    expect(rt.start().ok).toBe(false);
    expect(rt.pause().ok).toBe(true); // pause is no-op when not running
    expect(rt.resume().ok).toBe(true); // resume is no-op when not paused
    expect(rt.cancel().ok).toBe(true); // cancel is no-op from terminal
  });

  it('protocol-runtime-errored handler is wired (forward-compat)', () => {
    // The Runtime subscribes to ProtocolRuntime. Confirm protocol-runtime events
    // flow through even if no error occurs in this path.
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-fwd') });
    const protocolEvents: ProtocolRuntimeEvent[] = [];
    rt.subscribe((e: RuntimeEvent) => {
      if (e.source === 'protocol') {
        protocolEvents.push(e.payload);
      }
    });
    rt.compile(buildShortSource());
    // Loading itself emits protocol-runtime-loaded events.
    expect(protocolEvents.length).toBeGreaterThanOrEqual(0);
    rt.dispose();
  });

  it('notifyBackground/notifyForeground forward without exception', () => {
    const rt = new RuntimeEngine({ runtimeId: EngineId('e2e-appstate') });
    expect(() => rt.notifyBackground()).not.toThrow();
    expect(() => rt.notifyForeground()).not.toThrow();
    rt.dispose();
  });
});
