/**
 * Protocol interfaces — ProtocolSource, ExecutionPlan, CompilerResult,
 * ValidationResult.
 *
 * These describe how protocols are loaded, validated, compiled, and
 * executed. Implementations will live in @core/protocol-engine.
 */

import type { ProtocolId } from '../value-objects/ids';
import type { SemanticVersion } from '../value-objects/version';
import type { Duration, Iso8601 } from '../value-objects/numeric';
import type { BreathPhase, CurveType } from '../enums/breath';
import type { EngineId } from '../value-objects/ids';
import type { Result } from '../patterns/result';
import type { Failure } from '../patterns/failure';
import type { CompilationError, ValidationError } from '../errors/base';

// =============================================================================
// ProtocolSource
// =============================================================================

/**
 * Raw protocol source — JSON, Markdown, or other serialized form.
 */
export type ProtocolSourceFormat = 'json' | 'markdown' | 'toml' | 'yaml';

export interface ProtocolSource {
  readonly format: ProtocolSourceFormat;
  readonly raw: string;
  readonly origin?: string;
  readonly fetchedAt?: Iso8601;
}

/**
 * Loads protocol sources from various origins (filesystem, network,
 * embedded bundle).
 */
export interface ProtocolSourceLoader {
  load(id: ProtocolId, version: SemanticVersion): Promise<Result<ProtocolSource, ValidationError>>;
  loadFromString(raw: string, format: ProtocolSourceFormat): ProtocolSource;
  available(): readonly { readonly id: ProtocolId; readonly version: SemanticVersion }[];
}

// =============================================================================
// ExecutionPlan
// =============================================================================

/**
 * PhaseStep — a single phase in an execution plan.
 */
export interface PhaseStep {
  readonly index: number;
  readonly phase: BreathPhase;
  readonly duration: Duration;
  readonly curve: CurveType;
}

/**
 * ExecutionPlan — compiled, executable representation of a protocol.
 */
export interface ExecutionPlan {
  readonly protocolId: ProtocolId;
  readonly version: SemanticVersion;
  readonly phases: readonly PhaseStep[];
  readonly totalDuration: Duration;
  readonly cycles: number;
  readonly compiledAt: Iso8601;
  readonly compiledBy: EngineId;
}

// =============================================================================
// CompilerResult
// =============================================================================

/**
 * CompilerResult — outcome of compiling a protocol source into an
 * ExecutionPlan. May include non-blocking warnings.
 */
export interface CompilerResult {
  readonly plan: ExecutionPlan | null;
  readonly failures: readonly Failure[];
  readonly warnings: readonly Failure[];
}

// =============================================================================
// ValidationResult
// =============================================================================

/**
 * ValidationResult — outcome of validating a ProtocolSource or
 * ExecutionPlan against schema and rules.
 */
export interface ValidationResult {
  readonly valid: boolean;
  readonly failures: readonly Failure[];
}

/**
 * Compiler — transforms a ProtocolSource into an ExecutionPlan.
 */
export interface Compiler {
  compile(source: ProtocolSource): Result<CompilerResult, CompilationError>;
  validate(source: ProtocolSource): ValidationResult;
}