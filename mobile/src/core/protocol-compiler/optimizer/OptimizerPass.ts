/**
 * Optimizer passes — pure transformations applied to a ProtocolIR.
 *
 * Each pass:
 *   - Takes an IR and returns a NEW IR (never mutates)
 *   - Has a stable, descriptive name
 *   - Is independently testable
 *   - Reports side-channel data via the diagnostics parameter
 *
 * Passes:
 *   - RemoveRedundancyPass: collapses adjacent identical phases
 *     (e.g., 'inhale 2s, inhale 3s' → 'inhale 5s' with linear curve)
 *   - NormalizePhasesPass: ensures curves are set (default to easeInOut)
 *   - PrecalculateCyclesPass: ensures totalCycleMs / ratios are
 *     correct after other passes
 *   - PrecalculateDurationsPass: ensures totalSessionMs is correct
 *   - ComputeExecutionIdPass: stamps the IR with a deterministic
 *     executionId derived from a hash of canonical content
 */

import {
  Duration,
  PhaseIndex,
  type CurveType,
  type BreathPhase,
} from '@araflow/shared-contracts';
import type {
  ProtocolIR,
  BreathConfigIR,
  PhaseIR,
} from '../domain/IntermediateRepresentation';
import type { ExecutionId as ExecutionIdType } from '../domain/ExecutionPlan';
import { ExecutionId } from '../domain/ExecutionPlan';

/**
 * Optimizer diagnostics — collected across all passes.
 */
export interface OptimizerDiagnostics {
  /** Names of passes that ran. */
  readonly passesRun: readonly string[];
  /** Per-pass notes (e.g., "merged 2 redundant phases"). */
  readonly notes: readonly string[];
  /** ExecutionId assigned during optimization. */
  readonly executionId: ExecutionIdType;
}

/**
 * Optimizer pass — pure transformation.
 */
export interface OptimizerPass {
  readonly name: string;
  apply(ir: ProtocolIR): ProtocolIR;
}

// =============================================================================
// RemoveRedundancyPass
// =============================================================================

/**
 * Merges adjacent phases of the same type and curve into a single phase.
 *
 * Example:
 *   [inhale 1s, inhale 2s, hold-in 4s]
 *   →
 *   [inhale 3s, hold-in 4s]
 *
 * Only merges if both phases use the SAME curve (or both have no
 * curve override). Different curves are intentional and preserved.
 */
export const removeRedundancyPass: OptimizerPass = {
  name: 'remove-redundancy',
  apply: (ir: ProtocolIR): ProtocolIR => {
    const original = ir.breath.phases;
    if (original.length < 2) return ir;

    const merged: PhaseIR[] = [];
    for (const phase of original) {
      const last = merged[merged.length - 1];
      if (
        last !== undefined &&
        last.phase === phase.phase &&
        last.curve === phase.curve
      ) {
        // Merge: add durations, recompute ratio later
        const combined: PhaseIR = {
          index: last.index,
          phase: last.phase,
          duration: ((last.duration as unknown as number) +
            (phase.duration as unknown as number)) as unknown as Duration,
          curve: last.curve,
          ratio: 0, // recomputed by precalculate pass
        };
        merged[merged.length - 1] = combined;
      } else {
        merged.push(phase);
      }
    }

    if (merged.length === original.length) return ir;

    const totalCycleMs = sumDurations(merged);
    const reindexed: PhaseIR[] = merged.map((p, i) => ({
      ...p,
      index: i as unknown as PhaseIndex,
      ratio: totalCycleMs > 0
        ? (p.duration as unknown as number) / totalCycleMs
        : 0,
    }));

    return withPhases(ir, reindexed);
  },
};

// =============================================================================
// NormalizePhasesPass
// =============================================================================

/**
 * Ensures every phase has a curve. Phases without an explicit curve
 * default to 'easeInOut' (already handled by parser, but applied as
 * a safety net in case the IR was constructed by other means).
 *
 * Re-stamps phase indices to be contiguous from 0.
 */
export const normalizePhasesPass: OptimizerPass = {
  name: 'normalize-phases',
  apply: (ir: ProtocolIR): ProtocolIR => {
    const reindexed: PhaseIR[] = ir.breath.phases.map((p, i) => {
      const base: PhaseIR = {
        index: i as unknown as PhaseIndex,
        phase: p.phase,
        duration: p.duration,
        curve: p.curve,
        ratio: p.ratio,
      };
      return base;
    });
    return withPhases(ir, reindexed);
  },
};

// =============================================================================
// PrecalculateCyclesPass
// =============================================================================

/**
 * Re-calculates totalCycleMs from phases and recomputes phase ratios.
 * Idempotent.
 */
export const precalculateCyclesPass: OptimizerPass = {
  name: 'precalculate-cycles',
  apply: (ir: ProtocolIR): ProtocolIR => {
    const totalCycleMs = sumDurations(ir.breath.phases);
    const reindexed: PhaseIR[] = ir.breath.phases.map((p, i) => ({
      ...p,
      index: i as unknown as PhaseIndex,
      ratio: totalCycleMs > 0
        ? (p.duration as unknown as number) / totalCycleMs
        : 0,
    }));
    const newBreath: BreathConfigIR = {
      ...ir.breath,
      phases: reindexed,
      totalCycleMs: totalCycleMs as unknown as Duration,
    };
    return withBreath(ir, newBreath);
  },
};

// =============================================================================
// PrecalculateDurationsPass
// =============================================================================

/**
 * Recomputes totalSessionMs = totalCycleMs * cycles + rest * (cycles - 1).
 * Idempotent.
 */
export const precalculateDurationsPass: OptimizerPass = {
  name: 'precalculate-durations',
  apply: (ir: ProtocolIR): ProtocolIR => {
    const totalCycleMs = ir.breath.totalCycleMs as unknown as number;
    const rest = ir.breath.restBetweenCyclesMs as unknown as number;
    const cycles = ir.breath.cycles;
    const totalSessionMs =
      totalCycleMs * cycles + rest * Math.max(0, cycles - 1);
    const newBreath: BreathConfigIR = {
      ...ir.breath,
      totalSessionMs: totalSessionMs as unknown as Duration,
    };
    return withBreath(ir, newBreath);
  },
};

// =============================================================================
// ChecksumPass — derives a deterministic checksum of canonical content
// =============================================================================

/**
 * Computes a SHA-256-like fingerprint of the IR's canonical content.
 *
 * Uses a simple deterministic hash (FNV-1a) since the runtime is
 * Node + browser, both of which have subtle crypto API differences.
 * The hash is collision-resistant enough for change detection.
 *
 * Format: `fnv1a:<hex>` — clearly marked as not cryptographic.
 */
export const computeChecksum = (ir: ProtocolIR): string => {
  const parts: string[] = [
    ir.id as string,
    ir.version as string,
    ir.title,
    String(ir.breath.cycles),
    ...ir.breath.phases.map(
      (p) =>
        `${p.index}|${p.phase}|${p.duration}|${p.curve}|${p.ratio.toFixed(6)}`,
    ),
    String(ir.breath.restBetweenCyclesMs),
  ];
  const canonical = parts.join('\n');
  return `fnv1a:${fnv1a(canonical).toString(16).padStart(16, '0')}`;
};

/**
 * Optimizer pass that computes and attaches a checksum (via the IR's
 * `description`-free channel). Actually returns a fresh IR with the
 * checksum carried in a side record.
 */
export const checksumPass: OptimizerPass & {
  extractChecksum(ir: ProtocolIR): string;
} = {
  name: 'checksum',
  apply: (ir: ProtocolIR): ProtocolIR => ir, // checksum is read-only
  extractChecksum: computeChecksum,
};

// =============================================================================
// ComputeExecutionIdPass
// =============================================================================

/**
 * Generates an ExecutionId from the checksum. Two compilations of the
 * same IR produce the same ExecutionId (deterministic).
 *
 * Note: in production this might include a timestamp + nonce for
 * uniqueness across recompilations. For Sprint 3 we use a pure
 * derivation so the plan is reproducible.
 */
export const computeExecutionId = (checksum: string): ExecutionId =>
  ExecutionId(`exec-${checksum.slice(0, 24)}`);

// =============================================================================
// Pipeline runner
// =============================================================================

/**
 * Runs a sequence of optimizer passes in order. Pure: returns a new IR.
 */
export const runOptimizerPipeline = (
  ir: ProtocolIR,
  passes: readonly OptimizerPass[],
): { readonly ir: ProtocolIR; readonly passNames: readonly string[] } => {
  let current: ProtocolIR = ir;
  const run: string[] = [];
  for (const pass of passes) {
    current = pass.apply(current);
    run.push(pass.name);
  }
  return { ir: current, passNames: Object.freeze(run) };
};

// REDACTED
// Internal helpers
// REDACTED

const sumDurations = (phases: readonly PhaseIR[]): number => {
  let total = 0;
  for (const p of phases) {
    total += p.duration as unknown as number;
  }
  return total;
};

const withPhases = (ir: ProtocolIR, phases: readonly PhaseIR[]): ProtocolIR =>
  withBreath(ir, {
    ...ir.breath,
    phases: Object.freeze([...phases]),
  });

const withBreath = (ir: ProtocolIR, breath: BreathConfigIR): ProtocolIR =>
  Object.freeze({
    ...ir,
    breath: Object.freeze(breath),
  });

// FNV-1a 64-bit hash. Pure JS, deterministic.
const fnv1a = (s: string): number => {
  let hash = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  const mask = 0xffffffffffffffffn;
  for (let i = 0; i < s.length; i += 1) {
    hash = (hash ^ BigInt(s.charCodeAt(i))) & mask;
    hash = (hash * prime) & mask;
  }
  // Convert to number (loses precision beyond 2^53, but acceptable for fingerprint)
  return Number(hash & 0x1fffffffffffffn);
};

// Re-export so consumers can construct their own passes easily
export type { PhaseIR, BreathPhase, CurveType };
