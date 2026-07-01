/**
 * OrchestratorEvent — tagged-union of every event the Orchestrator
 * emits to its own listeners. The Orchestrator does NOT re-emit
 * Runtime events (consumers can subscribe to Runtime directly); it
 * emits only the events that are unique to its role as the bridge.
 *
 *   - 'orchestrator-attached'
 *   - 'orchestrator-detached'
 *   - 'orchestrator-replayed'
 *   - 'orchestrator-inconsistency'
 *   - 'orchestrator-disposed'
 */

import type { InconsistencyReport } from './InconsistencyReport';
import type { OrchestratorState } from './OrchestratorState';

export interface OrchestratorAttachedEvent {
  readonly type: 'orchestrator-attached';
  readonly monotonicMs: number;
  readonly orchestratorState: OrchestratorState;
}

export interface OrchestratorDetachedEvent {
  readonly type: 'orchestrator-detached';
  readonly monotonicMs: number;
  readonly orchestratorState: OrchestratorState;
}

export interface OrchestratorReplayedEvent {
  readonly type: 'orchestrator-replayed';
  readonly monotonicMs: number;
  readonly eventsReplayed: number;
  readonly targetSessionId: string;
}

export interface OrchestratorInconsistencyEvent {
  readonly type: 'orchestrator-inconsistency';
  readonly monotonicMs: number;
  readonly report: InconsistencyReport;
}

export interface OrchestratorDisposedEvent {
  readonly type: 'orchestrator-disposed';
  readonly monotonicMs: number;
}

export type OrchestratorEvent =
  | OrchestratorAttachedEvent
  | OrchestratorDetachedEvent
  | OrchestratorReplayedEvent
  | OrchestratorInconsistencyEvent
  | OrchestratorDisposedEvent;

export const ORCHESTRATOR_EVENT_TYPES: readonly OrchestratorEvent['type'][] = [
  'orchestrator-attached',
  'orchestrator-detached',
  'orchestrator-replayed',
  'orchestrator-inconsistency',
  'orchestrator-disposed',
] as const;

export type OrchestratorEventListener = (event: OrchestratorEvent) => void;
export type OrchestratorUnsubscribe = () => void;

export const isOrchestratorEvent = (value: unknown): value is OrchestratorEvent => {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const v = value as { type?: unknown };
  if (typeof v.type !== 'string') {
    return false;
  }
  return (ORCHESTRATOR_EVENT_TYPES as readonly string[]).includes(v.type);
};
