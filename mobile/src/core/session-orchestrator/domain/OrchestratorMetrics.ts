/**
 * OrchestratorMetrics — derived counters for the Orchestrator.
 *
 * Pure projection; computed lazily on each call.
 *
 *   - eventsProcessed   — total Runtime events forwarded to Session.
 *   - eventsSkipped     — Runtime events not mapped (e.g. timer/breath raw).
 *   - inconsistencies   — total InconsistencyReports emitted.
 *   - replays           — total completed replays.
 *   - perKindCounts     — counters grouped by InconsistencyKind.
 */

import {
  EMPTY_INCONSISTENCY_REPORTS,
  type InconsistencyKind,
  type InconsistencyReport,
} from './InconsistencyReport';

export interface OrchestratorMetrics {
  readonly eventsProcessed: number;
  readonly eventsSkipped: number;
  readonly inconsistencies: number;
  readonly replays: number;
  readonly perKindCounts: Readonly<Record<InconsistencyKind, number>>;
}

const emptyKindCounts = (): Readonly<Record<InconsistencyKind, number>> =>
  Object.freeze({
    'out-of-order': 0,
    'impossible-state': 0,
    'invalid-cycle': 0,
    'invalid-phase': 0,
    divergence: 0,
  });

export const EMPTY_ORCHESTRATOR_METRICS: OrchestratorMetrics = Object.freeze({
  eventsProcessed: 0,
  eventsSkipped: 0,
  inconsistencies: 0,
  replays: 0,
  perKindCounts: emptyKindCounts(),
});

export const computeOrchestratorMetrics = (input: {
  readonly eventsProcessed: number;
  readonly eventsSkipped: number;
  readonly reports: readonly InconsistencyReport[];
  readonly replays: number;
}): OrchestratorMetrics => {
  const counts: Record<InconsistencyKind, number> = {
    'out-of-order': 0,
    'impossible-state': 0,
    'invalid-cycle': 0,
    'invalid-phase': 0,
    divergence: 0,
  };
  for (const report of input.reports) {
    counts[report.kind] += 1;
  }
  return Object.freeze({
    eventsProcessed: input.eventsProcessed,
    eventsSkipped: input.eventsSkipped,
    inconsistencies: input.reports.length,
    replays: input.replays,
    perKindCounts: Object.freeze(counts),
  });
};

// Re-export for consumers.
export { EMPTY_INCONSISTENCY_REPORTS };
