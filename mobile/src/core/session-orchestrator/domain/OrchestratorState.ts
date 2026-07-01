/**
 * OrchestratorState — finite state machine for the SessionOrchestrator.
 *
 * 4 states:
 *   - 'detached'   — orchestrator constructed; no Runtime subscription active.
 *   - 'attached'   — Runtime events are being forwarded to the Session.
 *   - 'replaying'  — a replay is in progress (transient; goes back to 'attached' or 'detached').
 *   - 'disposed'   — terminal; orchestrator cannot be reused.
 *
 * The Orchestrator does NOT have its own session lifecycle FSM. It only
 * tracks whether it is actively bridging the Runtime and the Session.
 */

export type OrchestratorState = 'detached' | 'attached' | 'replaying' | 'disposed';

export const ORCHESTRATOR_STATES: readonly OrchestratorState[] = [
  'detached',
  'attached',
  'replaying',
  'disposed',
] as const;

export const TERMINAL_ORCHESTRATOR_STATES: readonly OrchestratorState[] = ['disposed'] as const;
export const ACTIVE_ORCHESTRATOR_STATES: readonly OrchestratorState[] = [
  'detached',
  'attached',
  'replaying',
] as const;

export const isOrchestratorState = (value: unknown): value is OrchestratorState =>
  typeof value === 'string' && (ORCHESTRATOR_STATES as readonly string[]).includes(value);

export const isTerminalOrchestratorState = (state: OrchestratorState): boolean =>
  (TERMINAL_ORCHESTRATOR_STATES as readonly OrchestratorState[]).includes(state);

export const legalOrchestratorTransitions = (
  from: OrchestratorState,
): readonly OrchestratorState[] => {
  switch (from) {
    case 'detached':
      return ['attached', 'replaying', 'disposed'];
    case 'attached':
      return ['detached', 'replaying', 'disposed'];
    case 'replaying':
      return ['attached', 'detached', 'disposed'];
    case 'disposed':
      return [];
  }
};

export const canOrchestratorTransition = (
  from: OrchestratorState,
  to: OrchestratorState,
): boolean => (legalOrchestratorTransitions(from) as readonly OrchestratorState[]).includes(to);
