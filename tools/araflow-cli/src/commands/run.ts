/**
 * run command — executes a plan using the real Timer Engine + Breath Engine
 * in parallel with the ProtocolRuntime.
 *
 * This is the proof that the four engines wire up end-to-end:
 *
 *   1. Compile plan (ProtocolCompiler)
 *   2. Create TimerEngine (real, wall-clock)
 *   3. Start timer (Breath Engine requires it running)
 *   4. Construct BreathEngine from the plan (N-phase → BreathCycleConfig)
 *   5. Construct ProtocolRuntime with TimerLike adapter wrapping TimerEngine
 *   6. Subscribe to all three event streams (timer / breath / protocol)
 *   7. Load + start the runtime
 *   8. Wait for completion (or timeout)
 *   9. Stop everything, print summary
 *
 * Drift = actualElapsed - plannedDuration (from the plan). Negative drift
 * means we finished earlier than planned (rare); positive drift means
 * Timer Engine slowed down (more common).
 */

import chalk from 'chalk';
import {
  ProtocolCompiler,
  ProtocolRuntime,
  type ProtocolRuntimeEvent,
} from '@core/protocol-compiler';
import { createTimerEngine, type TimerEvent } from '@core/timer-engine';
import { createBreathEngine, type BreathEvent } from '@core/breath-engine';
import { createTimerLikeAdapter, planToBreathConfig } from '@core/runtime';
import { CLI_COMPILER_ID, CLI_RUNTIME_ID } from '../util/engine-id';
import { loadProtocolSource } from '../io/load-source';
import { monotonicNowNs } from '../util/clock';
import { formatRuntimeEventStream, type RuntimeEventLine } from '../formatters/timeline';
import { formatSummary, type SessionSummary } from '../formatters/summary';
import { toJson } from '../formatters/json';

export interface RunOptions {
  readonly filepath: string;
  readonly json?: boolean;
  readonly maxDurationMs?: number;
  readonly quiet?: boolean;
}

interface CollectedRun {
  readonly plan: import('@core/protocol-compiler').ProtocolExecutionPlan;
  readonly events: readonly RuntimeEventLine[];
  readonly phasesObserved: number;
  readonly cycleTransitions: number;
  readonly stoppedReason: 'completed' | 'cancelled' | 'errored' | 'timeout';
  readonly actualMs: number;
}

const collectRun = async (
  filepath: string,
  maxDurationMs: number,
  quiet: boolean,
): Promise<CollectedRun> => {
  const source = loadProtocolSource(filepath);
  const compiler = new ProtocolCompiler({ compiledBy: CLI_COMPILER_ID });
  const compileResult = compiler.compile(source);
  if (compileResult.plan === null) {
    throw new Error('Compilation failed: see warnings above.');
  }
  const plan = compileResult.plan;
  const plannedDurationMs = plan.totalDuration as unknown as number;

  // --- Timer Engine (real, wall-clock)
  const timer = createTimerEngine();
  const timerStartNs = monotonicNowNs();

  // --- Breath Engine (4-phase rigid; we coerce the N-phase plan to it)
  const breathConfig = planToBreathConfig(plan);
  const breath = createBreathEngine({
    monotonic: { now: () => Number(monotonicNowNs() / 1_000_000n) },
    timerEngine: timer,
    config: breathConfig,
  });
  // Override internal engineId for log clarity (best-effort; BreathEngine
  // doesn't expose an id setter, so we keep its default id).

  // --- ProtocolRuntime driven by TimerEngine via TimerLike adapter
  const runtime = new ProtocolRuntime({
    runtimeId: CLI_RUNTIME_ID,
    timer: createTimerLikeAdapter(timer),
  });

  // --- Collect all three streams
  const events: RuntimeEventLine[] = [];

  const unsubTimer = timer.subscribe((e: TimerEvent) => {
    if (!quiet) events.push({ t: 0, stream: 'timer', summary: `timer ${e.type}` });
  });
  const unsubBreath = breath.subscribe((e: BreathEvent) => {
    if (!quiet) {
      const summary = 'phase' in e && e.phase !== undefined ? `phase=${e.phase}` : e.type;
      events.push({ t: 0, stream: 'breath', summary: `${e.type} ${summary}` });
    }
  });

  let phasesObserved = 0;
  let cycleTransitions = 0;
  const unsubRuntime = runtime.subscribe((e: ProtocolRuntimeEvent) => {
    if (e.type === 'protocol-runtime-phase-changed') {
      phasesObserved += 1;
    } else if (e.type === 'protocol-runtime-cycle-completed') {
      cycleTransitions += 1;
    }
    if (!quiet) {
      const summary = summariseRuntime(e);
      events.push({ t: 0, stream: 'protocol', summary });
    }
  });

  // Start the timer first (Breath Engine requires it)
  timer.start();
  breath.start();

  const loadResult = runtime.load(plan);
  if (!loadResult.ok) {
    unsubTimer();
    unsubBreath();
    unsubRuntime();
    timer.stop();
    breath.cancel();
    throw new Error(`Runtime load failed: ${loadResult.error.code}`);
  }
  const startResult = runtime.start();
  if (!startResult.ok) {
    unsubTimer();
    unsubBreath();
    unsubRuntime();
    timer.stop();
    breath.cancel();
    throw new Error(`Runtime start failed: ${startResult.error.code}`);
  }

  // Wait until runtime completes (or timeout)
  const deadline = Math.max(plannedDurationMs * 2, maxDurationMs);
  const pollIntervalMs = 50;
  let waitedMs = 0;
  while (runtime.state !== 'completed' && runtime.state !== 'stopped' && waitedMs < deadline) {
    await sleep(pollIntervalMs);
    waitedMs += pollIntervalMs;
  }

  const stoppedReason: CollectedRun['stoppedReason'] =
    runtime.state === 'completed'
      ? 'completed'
      : runtime.state === 'errored'
        ? 'errored'
        : waitedMs >= deadline
          ? 'timeout'
          : 'cancelled';

  const actualMs = Number((monotonicNowNs() - timerStartNs) / 1_000_000n);

  // Cleanup
  if (runtime.state === 'running') {
    runtime.stop();
  }
  breath.cancel();
  if (timer.getState() === 'running') {
    timer.stop();
  }
  unsubTimer();
  unsubBreath();
  unsubRuntime();

  return {
    plan,
    events,
    phasesObserved,
    cycleTransitions,
    stoppedReason,
    actualMs,
  };
};

export const summariseRuntime = (e: ProtocolRuntimeEvent): string => {
  switch (e.type) {
    case 'protocol-runtime-started':
      return `started id=${e.executionId}`;
    case 'protocol-runtime-paused':
      return `paused at=${e.atElapsedMs}ms`;
    case 'protocol-runtime-resumed':
      return `resumed pausedFor=${e.pausedForMs}ms`;
    case 'protocol-runtime-tick':
      return `tick t=${e.elapsedMs}ms cyc=${e.cycleIndex} ph=${e.phase} prog=${e.phaseProgress.toFixed(2)}`;
    case 'protocol-runtime-phase-changed':
      return `phase→${e.currentPhase} (cycle ${e.cycleIndex})`;
    case 'protocol-runtime-cycle-completed':
      return `cycle ${e.cycleIndex} done`;
    case 'protocol-runtime-completed':
      return `completed totalElapsed=${e.totalElapsedMs}ms`;
    case 'protocol-runtime-stopped':
      return `stopped reason=${e.reason}`;
    case 'protocol-runtime-errored':
      return `errored code=${e.code}`;
    default:
      return 'unknown';
  }
};

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

export const runCommand = async (opts: RunOptions): Promise<number> => {
  const maxDurationMs = opts.maxDurationMs ?? 5 * 60_000;
  const collected = await collectRun(opts.filepath, maxDurationMs, opts.quiet === true);

  const plannedDurationMs = collected.plan.totalDuration as unknown as number;
  const driftMs = collected.actualMs - plannedDurationMs;

  if (opts.json === true) {
    process.stdout.write(
      toJson({
        ok: collected.stoppedReason === 'completed',
        filepath: opts.filepath,
        executionId: collected.plan.executionId,
        plannedDurationMs,
        actualDurationMs: collected.actualMs,
        driftMs,
        phasesObserved: collected.phasesObserved,
        cycleTransitions: collected.cycleTransitions,
        stoppedReason: collected.stoppedReason,
        eventCount: collected.events.length,
      }) + '\n',
    );
    return collected.stoppedReason === 'completed' ? 0 : 3;
  }

  process.stdout.write(chalk.bold.green(`✓ Ran ${opts.filepath}\n\n`));
  if (!opts.quiet) {
    process.stdout.write(formatRuntimeEventStream(collected.events));
  }

  const summary: SessionSummary = {
    executionId: collected.plan.executionId,
    title: 'real-time run',
    cycles: collected.plan.cycles,
    totalPhases: collected.plan.phases.length * collected.plan.cycles,
    plannedDurationMs,
    actualDurationMs: collected.actualMs,
    driftMs,
    phasesObserved: collected.phasesObserved,
    cycleTransitionsObserved: collected.cycleTransitions,
    completedNaturally: collected.stoppedReason === 'completed',
    stoppedReason: collected.stoppedReason,
  };
  process.stdout.write(formatSummary(summary));

  return collected.stoppedReason === 'completed' ? 0 : 3;
};
