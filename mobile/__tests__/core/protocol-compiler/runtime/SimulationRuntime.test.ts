/**
 * SimulationRuntime tests.
 */

import { ProtocolCompiler } from '../../../../src/core/protocol-compiler/compiler/ProtocolCompiler';
import { JsonSource } from '../../../../src/core/protocol-compiler/domain/ProtocolSource';
import { SimulationRuntime } from '../../../../src/core/protocol-compiler/runtime/SimulationRuntime';
import type { Clock } from '@araflow/shared-contracts';
import { EngineId } from '@araflow/shared-contracts';

const COMPILER_ID = EngineId('protocol-compiler');

const validJson = (): string =>
  JSON.stringify({
    $schema: 'https://araflow.app/schemas/protocol/v1.json',
    id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    version: '1.0.0',
    title: 'Test',
    breath: {
      cycles: 2,
      phases: [
        { type: 'inhale', durationMs: 1000 },
        { type: 'exhale', durationMs: 1000 },
      ],
    },
  });

class FakeClock implements Clock {
  public t = 0;
  public now(): number {
    return this.t;
  }
  public wallNow(): number {
    return this.t;
  }
}

const compilePlan = () => {
  const compiler = new ProtocolCompiler({ compiledBy: COMPILER_ID, now: () => 1_700_000_000_000 });
  const result = compiler.compile(JsonSource(validJson()));
  if (result.plan === null) {
    throw new Error('compile failed');
  }
  return result.plan;
};

describe('SimulationRuntime', () => {
  describe('runToCompletion', () => {
    it('produces a complete report', () => {
      const plan = compilePlan();
      const clock = new FakeClock();
      const sim = new SimulationRuntime(plan, clock);
      const report = sim.runToCompletion();
      expect(report.executionId).toBe(plan.executionId);
      expect(report.totalCycles).toBe(2);
      expect(report.totalDurationMs).toBeGreaterThan(0);
      expect(report.cycles.length).toBeGreaterThan(0);
      expect(report.phases.length).toBeGreaterThan(0);
    });

    it('invokes onPhaseChange callback', () => {
      const plan = compilePlan();
      const clock = new FakeClock();
      const events: string[] = [];
      const sim = new SimulationRuntime(plan, clock, {
        onPhaseChange: (r) => events.push(r.phase),
      });
      sim.runToCompletion();
      expect(events.length).toBeGreaterThan(0);
    });

    it('invokes onCycleComplete callback', () => {
      const plan = compilePlan();
      const clock = new FakeClock();
      let cycles = 0;
      const sim = new SimulationRuntime(plan, clock, {
        onCycleComplete: () => {
          cycles += 1;
        },
      });
      sim.runToCompletion();
      expect(cycles).toBeGreaterThan(0);
    });

    it('produces frozen arrays', () => {
      const plan = compilePlan();
      const sim = new SimulationRuntime(plan, new FakeClock());
      const report = sim.runToCompletion();
      expect(Object.isFrozen(report.cycles)).toBe(true);
      expect(Object.isFrozen(report.phases)).toBe(true);
    });
  });

  describe('estimates', () => {
    it('estimatePhaseTransitions returns cycles * phases', () => {
      const plan = compilePlan();
      const sim = new SimulationRuntime(plan, new FakeClock());
      expect(sim.estimatePhaseTransitions()).toBe(plan.cycles * plan.phases.length);
    });

    it('estimateCycles returns the plan cycles', () => {
      const plan = compilePlan();
      const sim = new SimulationRuntime(plan, new FakeClock());
      expect(sim.estimateCycles()).toBe(plan.cycles);
    });
  });

  describe('tick granularity', () => {
    it('respects custom tickMs', () => {
      const plan = compilePlan();
      const clock = new FakeClock();
      const sim = new SimulationRuntime(plan, clock, { tickMs: 500 });
      const report = sim.runToCompletion();
      expect(report.totalDurationMs).toBeGreaterThan(0);
    });
  });
});