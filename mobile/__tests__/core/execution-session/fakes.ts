/**
 * Test fixtures for ExecutionSession tests.
 *
 * Provides a controllable monotonic clock and a helper to build a
 * valid ProtocolExecutionPlan with sensible defaults.
 */

import { EngineId, ProtocolId, Duration, SessionId } from '@araflow/shared-contracts';

import {
  buildExecutionPlan,
  type PlanPhaseStep,
  type ProtocolExecutionPlan,
  type ExecutionId,
} from '@core/protocol-compiler';

/** Mutable fake clock — tests advance time explicitly. */
export class FakeClock {
  private current = 0;

  public now = (): number => this.current;

  public advance = (ms: number): void => {
    this.current += ms;
  };

  public set = (ms: number): void => {
    this.current = ms;
  };
}

/**
 * Build a sessionId. Argument is a counter suffix used to make ids
 * unique across tests; ULID is constructed from a valid 24-char base
 * and a 2-char numeric suffix (Crockford ULID charset: 0-9 A-Z minus
 * I, L, O, U).
 */
let sessionCounter = 0;
export const fakeSessionId = (_label = 's'): SessionId => {
  sessionCounter += 1;
  const suffix = (sessionCounter % 100).toString().padStart(2, '0');
  const raw = `01ARZ3NDEKTSV4RRFFQ69G5F${suffix}`;
  return SessionId(raw);
};

/** Plan with cycles × 2 phases, all 1000ms each. */
export const fakePlan = (cycles = 4, phaseDurationMs = 1000): ProtocolExecutionPlan => {
  const phases: PlanPhaseStep[] = [];
  for (let i = 0; i < cycles * 2; i += 1) {
    phases.push({
      index: i,
      phase: i % 2 === 0 ? 'inhaling' : 'exhaling',
      duration: Duration(phaseDurationMs),
      curve: 'linear',
    });
  }
  return buildExecutionPlan({
    executionId: '01HXYZ00000000000000000000' as ExecutionId,
    protocolId: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
    version: '1.0.0',
    schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
    compilerVersion: '1.0.0',
    title: 'test-plan',
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
    phases,
    cycles,
    totalCycleDuration: Duration(phaseDurationMs * 2),
    totalDuration: Duration(cycles * phaseDurationMs * 2),
    checksum: '0x0000000000000000',
    compiledAt: new Date(0).toISOString(),
    compiledBy: EngineId('test-compiler'),
  }) as ProtocolExecutionPlan;
};

/** ExecutionPlanId aligned with the default fake plan. */
export const fakePlanId = (): string => '01HXYZ00000000000000000000';
