/**
 * ExecutionPlanBuilder — converts a ProtocolIR into a ProtocolExecutionPlan.
 *
 * The plan is the FINAL artifact of compilation. Once built:
 *   - It is frozen (Object.freeze at construction)
 *   - It is the only input the runtime needs
 *   - It is byte-stable across runs (modulo executionId randomness)
 *
 * The builder:
 *   - Pulls phases from the optimized IR
 *   - Sets compilerVersion and compiledBy
 *   - Computes the ExecutionId (derived from checksum)
 *   - Embeds the checksum
 */

import type { ProtocolIR } from '../domain/IntermediateRepresentation';
import type { ProtocolExecutionPlan, PlanPhaseStep, ExecutionId } from '../domain/ExecutionPlan';
import {
  buildExecutionPlan,
  PROTOCOL_COMPILER_VERSION,
  PROTOCOL_PLAN_FORMAT_VERSION,
} from '../domain/ExecutionPlan';
import type { EngineId, PhaseIndex, Duration, Iso8601 } from '@araflow/shared-contracts';
import { checksumPass, computeExecutionId } from '../optimizer/OptimizerPass';

/**
 * Parameters for building an ExecutionPlan.
 */
export interface ExecutionPlanParams {
  /** The optimized IR. */
  readonly ir: ProtocolIR;
  /** EngineId of the compiler instance (for traceability). */
  readonly compiledBy: EngineId;
  /** Schema URI of the source document. */
  readonly schemaUri: string;
}

/**
 * Builds a ProtocolExecutionPlan from the IR.
 */
export const buildExecutionPlanFromIR = (
  params: ExecutionPlanParams,
): ProtocolExecutionPlan => {
  const checksum = checksumPass.extractChecksum(params.ir);
  const executionId: ExecutionId = computeExecutionId(checksum);

  const phases: PlanPhaseStep[] = params.ir.breath.phases.map((p) => ({
    index: p.index as unknown as PhaseIndex,
    phase: p.phase,
    duration: p.duration as unknown as Duration,
    curve: p.curve,
  }));

  return buildExecutionPlan({
    executionId,
    protocolId: params.ir.id,
    version: params.ir.version,
    schemaUri: params.schemaUri,
    compilerVersion: `${PROTOCOL_COMPILER_VERSION}+plan.${PROTOCOL_PLAN_FORMAT_VERSION}`,
    title: params.ir.title,
    metadata: params.ir.metadata,
    phases,
    cycles: params.ir.breath.cycles,
    totalDuration: params.ir.breath.totalSessionMs as unknown as Duration,
    totalCycleDuration: params.ir.breath.totalCycleMs as unknown as Duration,
    compiledAt: params.ir.compiledAt as unknown as Iso8601,
    compiledBy: params.compiledBy,
    checksum,
  });
};
