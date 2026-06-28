/**
 * IntermediateRepresentation (IR) — pure domain representation of a protocol.
 *
 * The IR is the canonical intermediate form between the source document
 * and the Execution Plan. It is:
 *   - Immutable (all fields readonly)
 *   - Domain-only (no JSON keys, no schema references, no infrastructure)
 *   - Self-contained (no callbacks, no streams, no mutable refs)
 *
 * After construction, the IR never changes. Optimizers produce new IRs;
 * they never mutate existing ones.
 */

import type {
  ProtocolId,
  SemanticVersion,
  Duration,
  Iso8601,
  BreathPhase,
  CurveType,
  PhaseIndex,
  CycleIndex,
} from '@araflow/shared-contracts';

/**
 * MetadataIR — authorial / regulatory metadata preserved intact.
 *
 * The compiler does NOT interpret these fields. They pass through to
 * the Execution Plan and onward to the application layer, which can
 * surface them in UI, audit logs, or regulatory reports.
 */
export interface MetadataIR {
  readonly author?: string;
  readonly language?: string;
  readonly references: readonly string[];
  readonly evidenceLevel?: string;
  readonly contraindications: readonly string[];
  readonly category?: string;
  readonly tags: readonly string[];
  readonly approvedAt?: Iso8601;
}

export const emptyMetadataIR = (): MetadataIR => ({
  references: [],
  contraindications: [],
  tags: [],
});

/**
 * PhaseIR — one phase in canonical form.
 *
 * `ratio` is the phase duration divided by the cycle duration, in [0, 1].
 * Useful for breath engines that scale phase durations to a session
 * cadence without re-computing proportions.
 */
export interface PhaseIR {
  readonly index: PhaseIndex;
  readonly phase: BreathPhase;
  readonly duration: Duration;
  readonly curve: CurveType;
  readonly ratio: number;
}

/**
 * BreathConfigIR — breath-specific configuration in canonical form.
 *
 * `totalCycleMs` is the sum of phase durations in one cycle.
 * `totalSessionMs` is the entire session duration including rests.
 * Both are pre-calculated so the runtime doesn't need to.
 */
export interface BreathConfigIR {
  readonly cycles: number;
  readonly phases: readonly PhaseIR[];
  readonly restBetweenCyclesMs: Duration;
  readonly totalCycleMs: Duration;
  readonly totalSessionMs: Duration;
}

/**
 * ProtocolIR — the canonical intermediate representation.
 *
 * Identity (`id`, `version`) is preserved. Metadata is preserved intact.
 * `compiledAt` records when the IR was built from the document.
 */
export interface ProtocolIR {
  readonly id: ProtocolId;
  readonly version: SemanticVersion;
  readonly title: string;
  readonly subtitle: string;
  readonly description: string;
  readonly metadata: MetadataIR;
  readonly breath: BreathConfigIR;
  readonly compiledAt: Iso8601;
}

/**
 * Constructs an empty PhaseIR. Used by IR builder for initial state
 * and by optimizers when stripping phases.
 */
export const emptyPhaseIR = (): PhaseIR => ({
  index: 0 as PhaseIndex,
  phase: 'inhaling',
  duration: 0 as Duration,
  curve: 'linear',
  ratio: 0,
});

/**
 * Returns the canonical cycle index for a given absolute cycle position.
 * Pure derivation; no side effects.
 */
export const computeCycleIndex = (n: number): CycleIndex => {
  if (!Number.isInteger(n) || n < 0) {
    return 0 as CycleIndex;
  }
  return n as CycleIndex;
};
