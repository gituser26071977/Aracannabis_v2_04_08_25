/**
 * ProtocolMigrationPipeline — migrates documents across schema versions.
 *
 * Pipeline:
 *   - Detects the source schema (via $schema field)
 *   - Applies a chain of migrations from source major to target major
 *   - Idempotent: applying twice produces the same result
 *   - Records a trace of applied migrations (for diagnostics)
 *
 * Sprint 3 only has ONE schema version (v1), so this pipeline is a
 * no-op pass-through with the trace machinery wired up. Future
 * sprints will register real migrations (v1 → v2, etc.).
 */

import type { ProtocolDocument } from '../domain/ProtocolDocument';
import {
  extractSchemaUri,
  isSchemaVersionCompatible,
  CURRENT_SCHEMA_MAJOR,
  isSupportedSchemaUri,
  buildSchemaUri,
  type SupportedSchemaUri,
} from '../domain/SchemaVersion';
import type { Failure } from '@araflow/shared-contracts';
import { Failure as makeFailure } from '@araflow/shared-contracts';

/**
 * Migration step — transforms one document shape into the next.
 */
export interface Migration {
  /** Source major version this migration applies to. */
  readonly fromMajor: number;
  /** Target major version this migration produces. */
  readonly toMajor: number;
  /** Human-readable name. */
  readonly name: string;
  /** Performs the transformation. Must be pure (no I/O, no mutation). */
  readonly apply: (doc: ProtocolDocument) => ProtocolDocument;
}

/**
 * Trace entry — records one migration step that was applied.
 */
export interface MigrationTraceEntry {
  readonly fromMajor: number;
  readonly toMajor: number;
  readonly name: string;
}

/**
 * Result of migration.
 */
export interface MigrationResult {
  readonly doc: ProtocolDocument;
  readonly trace: readonly MigrationTraceEntry[];
  readonly failures: readonly Failure[];
}

/**
 * Migration registry — collects all available migrations.
 *
 * Pure data; the pipeline picks from this registry.
 */
export interface MigrationRegistry {
  register(migration: Migration): void;
  available(): readonly Migration[];
}

export const createMigrationRegistry = (): MigrationRegistry => {
  const migrations: Migration[] = [];
  return Object.freeze({
    register: (m: Migration): void => {
      migrations.push(m);
    },
    available: (): readonly Migration[] => Object.freeze([...migrations]),
  });
};

/**
 * Picks the migration chain from `fromMajor` to `toMajor`.
 *
 * Returns null if no path exists. The chain is computed via BFS over
 * the registry.
 */
export const findMigrationChain = (
  fromMajor: number,
  toMajor: number,
  registry: MigrationRegistry,
): readonly Migration[] | null => {
  if (fromMajor === toMajor) return [];
  if (fromMajor > toMajor) return null;

  // BFS
  const visited = new Set<number>([fromMajor]);
  const cameFrom = new Map<number, Migration>();
  const queue: number[] = [fromMajor];
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (current === toMajor) {
      // Reconstruct path
      const chain: Migration[] = [];
      let n: number | undefined = current;
      while (n !== undefined && n !== fromMajor) {
        const m = cameFrom.get(n);
        if (m === undefined) break;
        chain.unshift(m);
        n = m.fromMajor;
      }
      return chain;
    }
    for (const m of registry.available()) {
      if (m.fromMajor === current && !visited.has(m.toMajor)) {
        visited.add(m.toMajor);
        cameFrom.set(m.toMajor, m);
        queue.push(m.toMajor);
      }
    }
  }
  return null;
};

/**
 * Migration pipeline — orchestrator.
 */
export class ProtocolMigrationPipeline {
  public constructor(
    private readonly registry: MigrationRegistry,
    private readonly targetMajor: number = CURRENT_SCHEMA_MAJOR,
  ) {}

  public migrate(doc: ProtocolDocument): MigrationResult {
    const sourceUri = doc.$schema;
    const failures: Failure[] = [];
    const trace: MigrationTraceEntry[] = [];

    // If the source declares a compatible schema, no migration needed
    if (
      sourceUri !== undefined &&
      isSupportedSchemaUri(sourceUri) &&
      isSchemaVersionCompatible(sourceUri, buildSchemaUri(this.targetMajor) as SupportedSchemaUri)
    ) {
      return { doc, trace, failures };
    }

    // Extract source major
    const sourceMajor = extractMajorFromUri(sourceUri);
    if (sourceMajor === null) {
      failures.push(
        makeFailure({
          code: 'migration_unknown_schema',
          message: `Cannot determine schema major from $schema "${String(sourceUri)}"`,
          severity: 'error',
          path: '$',
          context: { schema: String(sourceUri) },
        }),
      );
      return { doc, trace, failures };
    }

    if (sourceMajor === this.targetMajor) {
      // Same major, different URI — pass through
      return { doc, trace, failures };
    }

    const chain = findMigrationChain(sourceMajor, this.targetMajor, this.registry);
    if (chain === null) {
      failures.push(
        makeFailure({
          code: 'migration_no_path',
          message: `No migration path from schema v${sourceMajor} to v${this.targetMajor}`,
          severity: 'error',
          path: '$',
          context: { from: sourceMajor, to: this.targetMajor },
        }),
      );
      return { doc, trace, failures };
    }

    // Apply chain
    let current: ProtocolDocument = doc;
    for (const migration of chain) {
      try {
        current = migration.apply(current);
        trace.push({
          fromMajor: migration.fromMajor,
          toMajor: migration.toMajor,
          name: migration.name,
        });
      } catch (e) {
        failures.push(
          makeFailure({
            code: 'migration_apply_failed',
            message: `Migration ${migration.name} failed: ${String(e)}`,
            severity: 'error',
            path: '$',
            context: { migration: migration.name, error: String(e) },
          }),
        );
        return { doc: current, trace, failures };
      }
    }

    return { doc: current, trace, failures };
  }
}

/**
 * Extracts the major version number from a schema URI.
 * Returns null if it can't be parsed.
 */
export const extractMajorFromUri = (uri: unknown): number | null => {
  if (typeof uri !== 'string') return null;
  const match = /\/v(\d+)(?:\.json)?$/.exec(uri);
  if (match === null) return null;
  const captured = match[1];
  if (captured === undefined) return null;
  const n = Number(captured);
  return Number.isInteger(n) ? n : null;
};

/**
 * Sentinel migration — no-op. Useful for tests and as a default.
 */
export const noopMigration = (fromMajor: number, toMajor: number): Migration => ({
  fromMajor,
  toMajor,
  name: `noop-${fromMajor}-to-${toMajor}`,
  apply: (doc) => doc,
});

// Re-export for callers that need them
export { extractSchemaUri };
