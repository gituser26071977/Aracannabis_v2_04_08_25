/**
 * SessionState — the Aggregate Root finite state machine.
 *
 * Distinct from `RuntimeState` (10 states, engine-oriented) and
 * `ProtocolRuntimeState` (8 states). The Session represents the
 * user's view of an in-flight breathing session and includes
 * pre-flight states (idle, preparing) plus interruption semantics
 * not present at the engine level.
 *
 * Lifecycle:
 *
 *   idle ─start→ preparing ─→ running ⇄ paused
 *                                       ├→ completed
 *                                       ├→ cancelled
 *                                       ├→ interrupted
 *                                       └→ failed
 *
 * Terminal states: completed, cancelled, interrupted, failed.
 * Disposal is orthogonal — `dispose()` is always allowed.
 *
 * Invariant: a session can never leave a terminal state (no resurrection).
 */

export type SessionState =
  | 'idle'
  | 'preparing'
  | 'running'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'interrupted'
  | 'failed';

export const SESSION_STATES: readonly SessionState[] = [
  'idle',
  'preparing',
  'running',
  'paused',
  'completed',
  'cancelled',
  'interrupted',
  'failed',
] as const;

export const TERMINAL_SESSION_STATES: readonly SessionState[] = [
  'completed',
  'cancelled',
  'interrupted',
  'failed',
] as const;

export const ACTIVE_SESSION_STATES: readonly SessionState[] = [
  'idle',
  'preparing',
  'running',
  'paused',
] as const;

export const isSessionState = (value: unknown): value is SessionState =>
  typeof value === 'string' && (SESSION_STATES as readonly string[]).includes(value);

export const isTerminalSessionState = (state: SessionState): boolean =>
  (TERMINAL_SESSION_STATES as readonly SessionState[]).includes(state);

export const isActiveSessionState = (state: SessionState): boolean =>
  (ACTIVE_SESSION_STATES as readonly SessionState[]).includes(state);

/**
 * Returns the set of legal target states from a given state.
 *
 * Used by ExecutionSession to validate lifecycle transitions before
 * applying them. The matrix is intentionally small and explicit —
 * adding a state requires updating this table.
 */
export const legalTransitions = (from: SessionState): readonly SessionState[] => {
  switch (from) {
    case 'idle':
      return ['preparing'];
    case 'preparing':
      return ['running', 'cancelled', 'failed'];
    case 'running':
      return ['paused', 'completed', 'cancelled', 'interrupted', 'failed'];
    case 'paused':
      return ['running', 'cancelled', 'interrupted', 'failed'];
    case 'completed':
    case 'cancelled':
    case 'interrupted':
    case 'failed':
      return [];
  }
};

export const canTransition = (from: SessionState, to: SessionState): boolean =>
  (legalTransitions(from) as readonly SessionState[]).includes(to);
