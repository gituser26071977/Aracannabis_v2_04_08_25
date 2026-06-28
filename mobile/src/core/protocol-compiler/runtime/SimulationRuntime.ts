/**
 * SimulationRuntime — executes an Execution Plan WITHOUT the Timer Engine.
 *
 * Purpose:
 *   - Validate plans end-to-end without requiring wall-clock time
 *   - Run deterministic benchmarks (CI, perf regression detection)
 *   - Generate audit reports (every phase transition recorded)
 *   - Unit-test the phase machine
 *
 * Design:
 *   - Pure function: time advances via a Clock injected by the caller
 *   - Synchronous: runToCompletion() returns a complete report
 *   - No I/O, no side effects, no engine dependencies
 *
 * NOT for production use — the actual user-facing runtime is
 * ProtocolRuntime. This is a tool.
 */

import type {
  ProtocolExecutionPlan,
  PlanPhaseStep,
} from '../domain/ExecutionPlan';
import type { BreathPhase, Clock } from '@araflow/shared-contracts';

/**
 * PhaseRecord — one observed phase transition.
 */
export interface SimulationPhaseRecord {
  readonly cycleIndex: number;
  readonly phaseIndex: number;
  readonly phase: BreathPhase;
  readonly durationMs: number;
  readonly startedAtMs: number;
  readonly endedAtMs: number;
}

/**
 * CycleRecord — one observed cycle.
 */
export interface SimulationCycleRecord {
  readonly cycleIndex: number;
  readonly phases: readonly SimulationPhaseRecord[];
  readonly cycleDurationMs: number;
}

/**
 * SimulationReport — complete execution trace.
 */
export interface SimulationReport {
  readonly executionId: string;
  readonly protocolId: string;
  readonly version: string;
  readonly totalCycles: number;
  readonly totalPhases: number;
  readonly totalDurationMs: number;
  readonly cycles: readonly SimulationCycleRecord[];
  readonly phases: readonly SimulationPhaseRecord[];
  readonly checksum: string;
  readonly startedAt: string;
  readonly completedAt: string;
}

/**
 * Simulation options.
 *
 * `tickMs` controls the granularity of internal progression (smaller =
 * more precise but slower simulation; larger = faster but coarser).
 */
export interface SimulationOptions {
  readonly tickMs?: number;
  readonly onPhaseChange?: (record: SimulationPhaseRecord) => void;
  readonly onCycleComplete?: (record: SimulationCycleRecord) => void;
}

/**
 * SimulationRuntime — pure simulator.
 */
export class SimulationRuntime {
  private readonly plan: ProtocolExecutionPlan;
  private readonly clock: Clock;
  private readonly options: SimulationOptions;

  public constructor(plan: ProtocolExecutionPlan, clock: Clock, options: SimulationOptions = {}) {
    this.plan = plan;
    this.clock = clock;
    this.options = options;
  }

  /**
   * Runs the plan to completion synchronously.
   *
   * The simulated clock advances in `tickMs` steps (default 100ms).
   * Each phase transition and cycle completion is recorded.
   */
  public runToCompletion(): SimulationReport {
    const tickMs = this.options.tickMs ?? 100;
    const cycleMs = this.plan.totalCycleDuration as unknown as number;
    const totalMs = this.plan.totalDuration as unknown as number;
    const startedAtMs = this.clock.now();

    const phaseRecords: SimulationPhaseRecord[] = [];
    const cycleRecords: SimulationCycleRecord[] = [];
    let currentCyclePhases: SimulationPhaseRecord[] = [];

    let simulatedMs = 0;
    let lastPhaseIndex = -1;
    let lastCycleIndex = -1;

    while (simulatedMs < totalMs) {
      const cycleIndex = Math.min(this.plan.cycles - 1, Math.floor(simulatedMs / cycleMs));
      const inCycleMs = simulatedMs - cycleIndex * cycleMs;
      const phaseInfo = this.findPhaseAt(inCycleMs);

      if (phaseInfo.phaseIndex !== lastPhaseIndex || cycleIndex !== lastCycleIndex) {
        // Phase (or cycle) changed
        if (cycleIndex !== lastCycleIndex && lastCycleIndex !== -1) {
          // Cycle boundary: close out previous cycle, start new
          const cycleRecord: SimulationCycleRecord = {
            cycleIndex: lastCycleIndex,
            phases: currentCyclePhases,
            cycleDurationMs: cycleMs,
          };
          cycleRecords.push(cycleRecord);
          if (this.options.onCycleComplete !== undefined) {
            this.options.onCycleComplete(cycleRecord);
          }
          currentCyclePhases = [];
        }

        if (cycleIndex !== lastCycleIndex) {
          lastCycleIndex = cycleIndex;
          lastPhaseIndex = -1;
        }

        const phaseStep = this.plan.phases[phaseInfo.phaseIndex];
        if (phaseStep !== undefined) {
          const record: SimulationPhaseRecord = {
            cycleIndex,
            phaseIndex: phaseInfo.phaseIndex,
            phase: phaseStep.phase,
            durationMs: phaseStep.duration as unknown as number,
            startedAtMs: simulatedMs,
            endedAtMs: simulatedMs + (phaseStep.duration as unknown as number),
          };
          phaseRecords.push(record);
          currentCyclePhases.push(record);
          if (this.options.onPhaseChange !== undefined) {
            this.options.onPhaseChange(record);
          }
          lastPhaseIndex = phaseInfo.phaseIndex;
        }
      }

      simulatedMs += tickMs;
    }

    // Close out the final cycle if not already
    if (currentCyclePhases.length > 0) {
      const cycleRecord: SimulationCycleRecord = {
        cycleIndex: lastCycleIndex,
        phases: currentCyclePhases,
        cycleDurationMs: cycleMs,
      };
      cycleRecords.push(cycleRecord);
      if (this.options.onCycleComplete !== undefined) {
        this.options.onCycleComplete(cycleRecord);
      }
    }

    const completedAtMs = this.clock.now();
    return {
      executionId: this.plan.executionId,
      protocolId: this.plan.protocolId,
      version: this.plan.version,
      totalCycles: this.plan.cycles,
      totalPhases: phaseRecords.length,
      totalDurationMs: totalMs,
      cycles: Object.freeze(cycleRecords),
      phases: Object.freeze(phaseRecords),
      checksum: this.plan.checksum,
      startedAt: new Date(startedAtMs).toISOString(),
      completedAt: new Date(completedAtMs).toISOString(),
    };
  }

  /**
   * Returns the phase that is active at `inCycleMs` within a cycle.
   *
   * Pure function exposed for testing.
   */
  private findPhaseAt(inCycleMs: number): { phaseIndex: number; phase: PlanPhaseStep } {
    let acc = 0;
    for (let i = 0; i < this.plan.phases.length; i += 1) {
      const phase = this.plan.phases[i]!;
      const duration = phase.duration as unknown as number;
      if (inCycleMs < acc + duration) {
        return { phaseIndex: i, phase };
      }
      acc += duration;
    }
    // Fallback: last phase
    const last = this.plan.phases[this.plan.phases.length - 1];
    if (last === undefined) {
      throw new Error('Empty plan');
    }
    return { phaseIndex: this.plan.phases.length - 1, phase: last };
  }

  /**
   * Convenience: returns just the total number of phase transitions
   * the simulation would produce, without running the full simulation.
   */
  public estimatePhaseTransitions(): number {
    return this.plan.cycles * this.plan.phases.length;
  }

  /**
   * Convenience: returns the expected cycle count.
   */
  public estimateCycles(): number {
    return this.plan.cycles;
  }
}
