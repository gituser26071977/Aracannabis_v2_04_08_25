/**
 * @core/session-orchestrator — Session Orchestrator.
 *
 * The bridge between @core/runtime and @core/execution-session. Consumes
 * Runtime events, translates them into Session API calls, detects
 * inconsistencies, supports replay, and integrates with an in-memory
 * Recorder. Pure domain — no persistence, no UI, no network.
 *
 * Version: 1.0.0 — frozen upon completion of Sprint 6.
 *
 * Consumers must NOT import any internal module directly. Always import
 * from this barrel.
 */

export { SessionOrchestrator } from './application/SessionOrchestrator';
export type {
  SessionOrchestratorDeps,
  OrchestratorClock,
} from './application/SessionOrchestratorDeps';
export { SessionRecorder } from './application/SessionRecorder';
export {
  createOrchestratorEventStream,
  type OrchestratorEventStream,
} from './application/OrchestratorEventStream';

// --- Domain types ---
export {
  type OrchestratorState,
  ORCHESTRATOR_STATES,
  TERMINAL_ORCHESTRATOR_STATES,
  ACTIVE_ORCHESTRATOR_STATES,
  isOrchestratorState,
  isTerminalOrchestratorState,
  legalOrchestratorTransitions,
  canOrchestratorTransition,
} from './domain/OrchestratorState';
export {
  type OrchestratorEvent,
  type OrchestratorEventListener,
  type OrchestratorUnsubscribe,
  ORCHESTRATOR_EVENT_TYPES,
  isOrchestratorEvent,
} from './domain/OrchestratorEvent';
export {
  type InconsistencyReport,
  type InconsistencyKind,
  INCONSISTENCY_KINDS,
  isInconsistencyKind,
  EMPTY_INCONSISTENCY_REPORTS,
  freezeInconsistency,
  outOfOrderReport,
  impossibleStateReport,
  invalidCycleReport,
  invalidPhaseReport,
  divergenceReport,
} from './domain/InconsistencyReport';
export {
  type SessionRecording,
  RECORDING_VERSION,
  isSessionRecording,
} from './domain/SessionRecording';
export {
  type OrchestratorMetrics,
  EMPTY_ORCHESTRATOR_METRICS,
  computeOrchestratorMetrics,
} from './domain/OrchestratorMetrics';

// --- Utilities (re-exported from util/) ---
export { translateRuntimeEvent, type SessionAction } from './util/event-translator';
export { runConsistencyChecks, type ConsistencyCheckInput } from './util/consistency-checks';
export { replayInto } from './util/replay-reducer';
export { toJson, fromJson, type JsonSessionRecording } from './util/recording-format';

// --- Version ---
export const SESSION_ORCHESTRATOR_VERSION = '1.0.0' as const;
