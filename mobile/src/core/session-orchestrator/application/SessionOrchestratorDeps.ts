/**
 * SessionOrchestratorDeps — constructor options for SessionOrchestrator.
 *
 * The Orchestrator holds references to:
 *   - the Runtime (read-only — its public API only)
 *   - the Session (driven by Orchestrator API calls)
 *   - an optional listener error sink
 *   - an optional clock for monotonic timestamps
 *
 * Identity of the bridge is the (sessionId, runtimeEngineId) pair;
 * both must be present and consistent.
 */

import type { EngineId } from '@araflow/shared-contracts';

import type { ExecutionSession } from '@core/execution-session';
import type { RuntimeEngine } from '@core/runtime';

export type OrchestratorClock = () => number;

export interface SessionOrchestratorDeps {
  readonly runtime: RuntimeEngine;
  readonly session: ExecutionSession;
  readonly onListenerError?: (error: unknown) => void;
  readonly now?: OrchestratorClock;
}

export interface OrchestratorIdentity {
  readonly sessionId: string;
  readonly runtimeEngineId: EngineId;
}
