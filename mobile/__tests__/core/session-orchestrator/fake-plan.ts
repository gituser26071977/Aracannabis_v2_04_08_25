/**
 * Fake plan builder — produces a valid ProtocolExecutionPlan.
 */

import { EngineId, ProtocolId as Pid, Duration, PhaseIndex } from '@araflow/shared-contracts';

import {
  buildExecutionPlan,
  type PlanPhaseStep,
  type ProtocolExecutionPlan,
} from '@core/protocol-compiler';

export const fakePlan = (cycles = 4, phaseDurationMs = 1000): ProtocolExecutionPlan => {
  const phases: PlanPhaseStep[] = [];
  for (let i = 0; i < cycles * 2; i += 1) {
    phases.push({
      index: PhaseIndex(i),
      phase: i % 2 === 0 ? 'inhaling' : 'exhaling',
      duration: Duration(phaseDurationMs),
      curve: 'linear',
    });
  }
  return buildExecutionPlan({
    executionId: '01HXYZ00000000000000000000' as never,
    protocolId: Pid('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
    version: '1.0.0' as never,
    schemaUri: 'https://araflow.app/schemas/protocol/v1.json',
    compilerVersion: '1.0.0' as never,
    title: 'test-plan',
    metadata: {
      author: 'test',
      references: [],
      language: 'en',
      evidenceLevel: 'C',
      contraindications: [],
      category: 'test',
      tags: [],
      approvedAt: new Date(0).toISOString() as never,
    },
    phases,
    cycles,
    totalCycleDuration: Duration(phaseDurationMs * 2),
    totalDuration: Duration(cycles * phaseDurationMs * 2),
    checksum: '0x0000000000000000',
    compiledAt: new Date(0).toISOString() as never,
    compiledBy: EngineId('test-compiler'),
  }) as ProtocolExecutionPlan;
};
