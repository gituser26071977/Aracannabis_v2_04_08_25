/**
 * AraFlow — Protocol Compiler (public API)
 *
 * The first complete compiler of the AraFlow ecosystem. Transforms a
 * declarative protocol definition (JSON) into an immutable, serializable,
 * deterministic Execution Plan, then runs that plan through a decoupled
 * Runtime.
 *
 * Pipeline:
 *   Source → Parser → Validators → Migration → IR → Optimizer → Plan → Runtime
 *
 * Exports:
 *   - ProtocolCompiler: orchestrator
 *   - JsonProtocolParser: Sprint 3 parser (extensible for YAML/DSL)
 *   - SchemaValidator, SemanticValidator, VersionCompatibilityValidator
 *   - ProtocolMigrationPipeline + MigrationRegistry
 *   - IRBuilder
 *   - OptimizerPass + standard passes
 *   - ExecutionPlanBuilder
 *   - ProtocolRuntime + SimulationRuntime
 *   - ProtocolLinter
 *
 * Constraints:
 *   - No UI, React, RN, or platform-specific imports
 *   - Zero `any`, zero TODO, zero FIXME
 *   - 100% TypeScript strict
 *   - Deterministic output
 */

// =============================================================================
// Domain types
// =============================================================================

export type {
  ProtocolDocument,
  DocumentPhase,
  DocumentBreathConfig,
  DocumentMetadata,
  EvidenceLevel,
} from './domain/ProtocolDocument';

export { EVIDENCE_LEVELS, isEvidenceLevel } from './domain/ProtocolDocument';

export type {
  ProtocolSource,
  ProtocolSourceFormat,
} from './domain/ProtocolSource';

export { JsonSource, isProtocolSource } from './domain/ProtocolSource';

export type { ProtocolParser, ParserRegistry, ParserCapabilities } from './domain/ProtocolParser';
export { createParserRegistry } from './domain/ProtocolParser';

export type { ProtocolIR, BreathConfigIR, PhaseIR, MetadataIR } from './domain/IntermediateRepresentation';
export { emptyMetadataIR, computeCycleIndex } from './domain/IntermediateRepresentation';

export type {
  ProtocolExecutionPlan,
  PlanPhaseStep,
  PlanMetadata,
  ExecutionId as ExecutionIdType,
} from './domain/ExecutionPlan';
export {
  ExecutionId,
  buildExecutionPlan,
  PROTOCOL_COMPILER_VERSION,
  PROTOCOL_PLAN_FORMAT_VERSION,
} from './domain/ExecutionPlan';

export type { DocumentPhaseType } from './domain/DocumentPhaseType';
export {
  DOCUMENT_PHASE_TYPES,
  isDocumentPhaseType,
  toCanonicalPhase,
  fromCanonicalPhase,
} from './domain/DocumentPhaseType';

export type { DocumentCurveType } from './domain/DocumentCurve';

export {
  DOCUMENT_CURVE_TYPES,
  isDocumentCurveType,
  toCanonicalCurve,
  fromCanonicalCurve,
  isCanonicalCurve,
} from './domain/DocumentCurve';

export {
  SUPPORTED_SCHEMA_VERSIONS,
  DEFAULT_SCHEMA_URI,
  CURRENT_SCHEMA_MAJOR,
  isSupportedSchemaUri,
  isSchemaVersionCompatible,
  extractSchemaUri,
  buildSchemaUri,
} from './domain/SchemaVersion';

// =============================================================================
// Parser
// =============================================================================

export { JsonProtocolParser } from './parser/JsonProtocolParser';

// =============================================================================
// Validators
// =============================================================================

export {
  SchemaValidator,
  SemanticValidator,
  VersionCompatibilityValidator,
} from './validation/Validators';

// =============================================================================
// Migration
// =============================================================================

export type { Migration, MigrationRegistry, MigrationResult, MigrationTraceEntry } from './migration/ProtocolMigrationPipeline';
export {
  createMigrationRegistry,
  findMigrationChain,
  ProtocolMigrationPipeline,
  extractMajorFromUri,
  noopMigration,
} from './migration/ProtocolMigrationPipeline';

// =============================================================================
// IR Builder
// =============================================================================

export { buildIR, buildMetadata } from './ir/IRBuilder';

// =============================================================================
// Optimizer
// =============================================================================

export type { OptimizerPass, OptimizerDiagnostics } from './optimizer/OptimizerPass';
export {
  removeRedundancyPass,
  normalizePhasesPass,
  precalculateCyclesPass,
  precalculateDurationsPass,
  checksumPass,
  computeChecksum,
  computeExecutionId,
  runOptimizerPipeline,
} from './optimizer/OptimizerPass';

// =============================================================================
// Execution Plan builder
// =============================================================================

export type { ExecutionPlanParams } from './compiler/ExecutionPlanBuilder';
export { buildExecutionPlanFromIR } from './compiler/ExecutionPlanBuilder';

// =============================================================================
// Compiler
// =============================================================================

export type {
  CompilerConfig,
  CompilerDiagnostics,
  FullCompilerResult,
} from './compiler/ProtocolCompiler';
export { ProtocolCompiler, toSharedCompilerResult } from './compiler/ProtocolCompiler';

// =============================================================================
// Runtime
// =============================================================================

export type {
  ProtocolRuntimeState,
  ProtocolRuntimeEvent,
  ProtocolRuntimeListener,
  ProtocolRuntimeSnapshot,
  ProtocolRuntimeDeps,
  TimerLike,
  TimerLikeEvent,
} from './runtime/ProtocolRuntime';
export {
  ProtocolRuntime,
  PROTOCOL_RUNTIME_VERSION,
  PROTOCOL_RUNTIME_STATES,
  isProtocolRuntimeState,
} from './runtime/ProtocolRuntime';

export type {
  SimulationPhaseRecord,
  SimulationCycleRecord,
  SimulationReport,
  SimulationOptions,
} from './runtime/SimulationRuntime';
export { SimulationRuntime } from './runtime/SimulationRuntime';

// =============================================================================
// Linter
// =============================================================================

export type { LintRule } from './linter/ProtocolLinter';
export {
  ProtocolLinter,
  redundantStepsRule,
  invalidDurationRule,
  missingMetadataRule,
  emptyProtocolRule,
  checksumInconsistencyRule,
  unusualCycleCountRule,
  missingDescriptionRule,
} from './linter/ProtocolLinter';

// =============================================================================
// Version
// =============================================================================

export const PROTOCOL_COMPILER_PUBLIC_VERSION = '1.0.0' as const;
