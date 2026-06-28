/**
 * ProtocolCompiler — orchestrator that runs the full pipeline.
 *
 * Pipeline:
 *   1. Parser            (source format → ProtocolDocument)
 *   2. SchemaValidator   (structural rules)
 *   3. SemanticValidator (domain rules)
 *   4. CompatibilityValidator (version rules)
 *   5. Migration         (if needed)
 *   6. IRBuilder         (document → IR)
 *   7. Optimizer         (passes over IR)
 *   8. ExecutionPlanBuilder (IR → Plan)
 *   9. Linter            (warnings, never blocks)
 *
 * Returns a CompilerResult with:
 *   - plan: ProtocolExecutionPlan | null
 *   - failures: Failure[]   (blocking)
 *   - warnings: Failure[]   (non-blocking)
 *   - diagnostics: { parseTimeMs, validateTimeMs, optimizeTimeMs, totalTimeMs }
 *
 * Failures are accumulated — the compiler does NOT short-circuit on
 * the first error. Users get a complete report.
 */

import {
  type Result,
  type CompilerResult,
  type CompilationError,
} from '@araflow/shared-contracts';

import type { ProtocolSource } from '../domain/ProtocolSource';
import type { ProtocolDocument } from '../domain/ProtocolDocument';
import type { ProtocolExecutionPlan } from '../domain/ExecutionPlan';
import type { ProtocolParser, ParserRegistry } from '../domain/ProtocolParser';
import { createParserRegistry } from '../domain/ProtocolParser';
import { JsonProtocolParser } from '../parser/JsonProtocolParser';
import {
  SchemaValidator,
  SemanticValidator,
  VersionCompatibilityValidator,
} from '../validation/Validators';
import type { MigrationRegistry } from '../migration/ProtocolMigrationPipeline';
import { createMigrationRegistry, ProtocolMigrationPipeline } from '../migration/ProtocolMigrationPipeline';
import { buildIR } from '../ir/IRBuilder';
import type { OptimizerPass } from '../optimizer/OptimizerPass';
import {
  removeRedundancyPass,
  normalizePhasesPass,
  precalculateCyclesPass,
  precalculateDurationsPass,
  checksumPass,
} from '../optimizer/OptimizerPass';
import { buildExecutionPlanFromIR } from './ExecutionPlanBuilder';
import type { EngineId } from '@araflow/shared-contracts';
import { ProtocolLinter } from '../linter/ProtocolLinter';
import { CURRENT_SCHEMA_MAJOR } from '../domain/SchemaVersion';

/**
 * Diagnostics — timing and pass information collected during compilation.
 */
export interface CompilerDiagnostics {
  readonly parseTimeMs: number;
  readonly validateTimeMs: number;
  readonly migrateTimeMs: number;
  readonly buildIrTimeMs: number;
  readonly optimizeTimeMs: number;
  readonly lintTimeMs: number;
  readonly totalTimeMs: number;
  readonly optimizerPasses: readonly string[];
  readonly migrationTrace: readonly { readonly fromMajor: number; readonly toMajor: number; readonly name: string }[];
}

/**
 * Result of a full compilation.
 */
export interface FullCompilerResult {
  readonly plan: ProtocolExecutionPlan | null;
  readonly failures: readonly import('@araflow/shared-contracts').Failure[];
  readonly warnings: readonly import('@araflow/shared-contracts').Failure[];
  readonly diagnostics: CompilerDiagnostics;
}

/**
 * Configuration for the compiler.
 */
export interface CompilerConfig {
  readonly compiledBy: EngineId;
  readonly parsers?: ParserRegistry;
  readonly migrations?: MigrationRegistry;
  readonly optimizerPasses?: readonly OptimizerPass[];
  readonly compatibilityMajor?: number;
  readonly now?: () => number;
}

/**
 * ProtocolCompiler — the canonical entry point.
 *
 * Construct with a compiledBy EngineId. Reuse across compilations.
 */
export class ProtocolCompiler {
  private readonly compiledBy: EngineId;
  private readonly parserRegistry: ParserRegistry;
  private readonly migrationRegistry: MigrationRegistry;
  private readonly optimizerPasses: readonly OptimizerPass[];
  private readonly compatibilityMajor: number;
  private readonly now: () => number;
  private readonly schemaValidator: SchemaValidator;
  private readonly semanticValidator: SemanticValidator;
  private readonly compatibilityValidator: VersionCompatibilityValidator;
  private readonly linter: ProtocolLinter;

  public constructor(config: CompilerConfig) {
    this.compiledBy = config.compiledBy;
    this.parserRegistry = config.parsers ?? defaultParserRegistry();
    this.migrationRegistry = config.migrations ?? defaultMigrationRegistry();
    this.optimizerPasses =
      config.optimizerPasses ?? defaultOptimizerPasses();
    this.compatibilityMajor = config.compatibilityMajor ?? CURRENT_SCHEMA_MAJOR;
    this.now = config.now ?? Date.now;
    this.schemaValidator = new SchemaValidator();
    this.semanticValidator = new SemanticValidator();
    this.compatibilityValidator = new VersionCompatibilityValidator(this.compatibilityMajor);
    this.linter = new ProtocolLinter();
  }

  /**
   * Compiles a single ProtocolSource into an Execution Plan.
   */
  public compile(source: ProtocolSource): FullCompilerResult {
    const totalStart = this.now();
    const timings = {
      parseTimeMs: 0,
      validateTimeMs: 0,
      migrateTimeMs: 0,
      buildIrTimeMs: 0,
      optimizeTimeMs: 0,
      lintTimeMs: 0,
    };
    const failures: import('@araflow/shared-contracts').Failure[] = [];
    const warnings: import('@araflow/shared-contracts').Failure[] = [];

    // Step 1: Parse
    const parseStart = this.now();
    const parser = this.parserRegistry.resolve(source.format);
    if (parser === null) {
      failures.push({
        code: 'parser_not_registered',
        message: `No parser registered for format "${source.format}"`,
        severity: 'error',
        path: '$',
        context: { format: source.format },
      });
      const totalTimeMs = this.now() - totalStart;
      return {
        plan: null,
        failures: Object.freeze(failures),
        warnings: Object.freeze(warnings),
        diagnostics: {
          ...timings,
          parseTimeMs: this.now() - parseStart,
          totalTimeMs,
          optimizerPasses: Object.freeze([]),
          migrationTrace: Object.freeze([]),
        },
      };
    }
    const parseResult = parser.parse(source);
    timings.parseTimeMs = this.now() - parseStart;

    if (!parseResult.ok) {
      failures.push({
        code: parseResult.error.code,
        message: parseResult.error.message,
        severity: 'error',
        path: parseResult.error.path ?? '$',
        context: parseResult.error.context,
      });
      const totalTimeMs = this.now() - totalStart;
      return {
        plan: null,
        failures: Object.freeze(failures),
        warnings: Object.freeze(warnings),
        diagnostics: {
          ...timings,
          totalTimeMs,
          optimizerPasses: Object.freeze([]),
          migrationTrace: Object.freeze([]),
        },
      };
    }

    const doc: ProtocolDocument = parseResult.value;

    // Step 2-4: Validate
    const validateStart = this.now();
    failures.push(...this.schemaValidator.validate(doc));
    failures.push(...this.semanticValidator.validate(doc));
    failures.push(...this.compatibilityValidator.validate(doc));
    timings.validateTimeMs = this.now() - validateStart;

    if (hasBlockingFailures(failures)) {
      const totalTimeMs = this.now() - totalStart;
      return {
        plan: null,
        failures: Object.freeze(failures),
        warnings: Object.freeze(warnings),
        diagnostics: {
          ...timings,
          totalTimeMs,
          optimizerPasses: Object.freeze([]),
          migrationTrace: Object.freeze([]),
        },
      };
    }

    // Step 5: Migrate
    const migrateStart = this.now();
    const pipeline = new ProtocolMigrationPipeline(
      this.migrationRegistry,
      this.compatibilityMajor,
    );
    const migration = pipeline.migrate(doc);
    failures.push(...migration.failures);
    timings.migrateTimeMs = this.now() - migrateStart;

    if (hasBlockingFailures(failures)) {
      const totalTimeMs = this.now() - totalStart;
      return {
        plan: null,
        failures: Object.freeze(failures),
        warnings: Object.freeze(warnings),
        diagnostics: {
          ...timings,
          totalTimeMs,
          optimizerPasses: Object.freeze([]),
          migrationTrace: Object.freeze(migration.trace),
        },
      };
    }

    const migratedDoc = migration.doc;

    // Step 6: Build IR
    const buildIrStart = this.now();
    const ir = buildIR(migratedDoc, this.now);
    timings.buildIrTimeMs = this.now() - buildIrStart;

    // Step 7: Optimize
    const optimizeStart = this.now();
    let optimized = ir;
    const passesRun: string[] = [];
    for (const pass of this.optimizerPasses) {
      optimized = pass.apply(optimized);
      passesRun.push(pass.name);
    }
    // Ensure checksum is computed
    checksumPass.apply(optimized);
    timings.optimizeTimeMs = this.now() - optimizeStart;

    // Step 8: Build Execution Plan
    const plan = buildExecutionPlanFromIR({
      ir: optimized,
      compiledBy: this.compiledBy,
      schemaUri: migratedDoc.$schema,
    });

    // Step 9: Lint
    const lintStart = this.now();
    const lintFindings = this.linter.lint(migratedDoc, optimized, plan);
    warnings.push(...lintFindings);
    timings.lintTimeMs = this.now() - lintStart;

    const totalTimeMs = this.now() - totalStart;
    return {
      plan,
      failures: Object.freeze(failures),
      warnings: Object.freeze(warnings),
      diagnostics: {
        ...timings,
        totalTimeMs,
        optimizerPasses: Object.freeze(passesRun),
        migrationTrace: Object.freeze(migration.trace),
      },
    };
  }
}

// REDACTED
// Defaults
// REDACTED

const defaultParserRegistry = (): ParserRegistry => {
  const reg = createParserRegistry();
  const json: ProtocolParser = new JsonProtocolParser();
  reg.register(json);
  return reg;
};

const defaultMigrationRegistry = (): MigrationRegistry => createMigrationRegistry();

const defaultOptimizerPasses = (): readonly OptimizerPass[] =>
  Object.freeze([
    normalizePhasesPass,
    removeRedundancyPass,
    precalculateCyclesPass,
    precalculateDurationsPass,
  ]);

const hasBlockingFailures = (
  failures: readonly import('@araflow/shared-contracts').Failure[],
): boolean => failures.some((f) => f.severity === 'error' || f.severity === 'fatal');

// Re-export for consumers that need to convert FullCompilerResult
// to the shared-contracts CompilerResult shape.
export const toSharedCompilerResult = (
  full: FullCompilerResult,
): CompilerResult => ({
  plan: full.plan,
  failures: full.failures,
  warnings: full.warnings,
});

// Re-export so callers don't need a second import.
export type { Result, CompilationError };
