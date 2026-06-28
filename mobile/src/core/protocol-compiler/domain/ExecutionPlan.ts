/**
 * ExecutionPlan — the contract between the compiler and the runtime.
 *
 * The Execution Plan is:
 *   - Immutable (Object.freeze at construction)
 *   - Serializable (all values are primitives or readonly arrays)
 *   - Versioned (compilerVersion + protocolSchemaVersion)
 *   - Deterministic (same input → byte-identical output, modulo executionId)
 *   - Independent of UI (no React, no RN, no platform imports)
 *
 * The runtime consumes only this structure; it never touches the
 * source ProtocolDocument again.
 */

import type {
  ProtocolId,
  SemanticVersion,
  Duration,
  Iso8601,
  EngineId,
  BreathPhase,
  CurveType,
  PhaseIndex,
} from '@araflow/shared-contracts';
import type { MetadataIR } from './IntermediateRepresentation';

/**
 * ExecutionId — opaque identifier for one compilation output.
 *
 * Generated during optimization. Two compilations of the same protocol
 * produce different ExecutionIds (they are not checksums of the input).
 */
export type ExecutionId = string & { readonly __executionId: unique symbol };

export const ExecutionId = (raw: string): ExecutionId => raw as ExecutionId;

/**
 * PhaseStep — one step in the execution plan.
 *
 * Identical to shared-contracts ExecutionPlan PhaseStep but kept here
 * to keep the compiler's data model self-contained. The runtime maps
 * to the shared-contracts type when interacting with engines.
 */
export interface PlanPhaseStep {
  readonly index: PhaseIndex;
  readonly phase: BreathPhase;
  readonly duration: Duration;
  readonly curve: CurveType;
}

/**
 * PlanMetadata — metadata block carried by the execution plan.
 *
 * Identical shape to MetadataIR but re-exposed under a stable name so
 * downstream code can depend on this type without importing the IR.
 */
export type PlanMetadata = MetadataIR;

/**
 * ProtocolExecutionPlan — the canonical compiled output.
 */
export interface ProtocolExecutionPlan {
  /** Opaque identifier of this specific compilation. */
  readonly executionId: ExecutionId;
  /** Identifier of the source protocol. */
  readonly protocolId: ProtocolId;
  /** Semantic version of the source protocol. */
  readonly version: SemanticVersion;
  /** URI of the schema the source document declared. */
  readonly schemaUri: string;
  /** Version of the compiler that produced this plan. */
  readonly compilerVersion: string;
  /** Protocol title (for logs and reports). */
  readonly title: string;
  /** Compiled metadata block — preserved intact from source. */
  readonly metadata: PlanMetadata;
  /** Ordered phase steps. */
  readonly phases: readonly PlanPhaseStep[];
  /** Number of breath cycles in this session. */
  readonly cycles: number;
  /** Total session duration in ms (cycles * phases + rests). */
  readonly totalDuration: Duration;
  /** Duration of one breath cycle in ms. */
  readonly totalCycleDuration: Duration;
  /** ISO 8601 timestamp of compilation. */
  readonly compiledAt: Iso8601;
  /** EngineId of the compiler instance. */
  readonly compiledBy: EngineId;
  /** SHA-256 checksum of the canonical source. */
  readonly checksum: string;
}

/**
 * Builds and freezes a ProtocolExecutionPlan. Call this in the compiler
 * to ensure runtime immutability (not just type immutability).
 */
export const buildExecutionPlan = (
  params: Omit<ProtocolExecutionPlan, never>,
): ProtocolExecutionPlan => {
  // Build metadata conditionally to respect exactOptionalPropertyTypes
  const md = params.metadata;
  const metadata: PlanMetadata = Object.freeze({
    ...(md.author !== undefined ? { author: md.author } : {}),
    ...(md.language !== undefined ? { language: md.language } : {}),
    references: Object.freeze([...md.references]),
    ...(md.evidenceLevel !== undefined ? { evidenceLevel: md.evidenceLevel } : {}),
    contraindications: Object.freeze([...md.contraindications]),
    ...(md.category !== undefined ? { category: md.category } : {}),
    tags: Object.freeze([...md.tags]),
    ...(md.approvedAt !== undefined ? { approvedAt: md.approvedAt } : {}),
  });

  return Object.freeze({
    executionId: params.executionId,
    protocolId: params.protocolId,
    version: params.version,
    schemaUri: params.schemaUri,
    compilerVersion: params.compilerVersion,
    title: params.title,
    metadata,
    phases: Object.freeze(
      params.phases.map((p) =>
        Object.freeze({
          index: p.index,
          phase: p.phase,
          duration: p.duration,
          curve: p.curve,
        }),
      ),
    ),
    cycles: params.cycles,
    totalDuration: params.totalDuration,
    totalCycleDuration: params.totalCycleDuration,
    compiledAt: params.compiledAt,
    compiledBy: params.compiledBy,
    checksum: params.checksum,
  });
};

/**
 * PROTOCOL_COMPILER_VERSION — bumped on any change to compiler output.
 *
 * Used by runtime to detect older plans and decide on migration.
 */
export const PROTOCOL_COMPILER_VERSION = '1.0.0' as const;

/**
 * PROTOCOL_PLAN_FORMAT_VERSION — version of the ExecutionPlan shape.
 *
 * Separate from compiler version because the shape may evolve.
 */
export const PROTOCOL_PLAN_FORMAT_VERSION = '1.0.0' as const;
