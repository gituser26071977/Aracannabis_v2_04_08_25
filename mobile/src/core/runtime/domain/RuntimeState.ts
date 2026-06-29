/**
 * RuntimeState — Runtime-level finite state machine.
 *
 * Distinct from `ProtocolRuntimeState` (8 states) — Runtime owns the
 * full lifecycle including disposal, and translates `protocol-runtime-errored`
 * events (which are declared but never emitted by ProtocolRuntime) plus
 * compile failures into a single `'errored'` state.
 *
 * Lifecycle:
 *   uninitialized → loaded → starting → running ⇄ paused
 *                                       → stopping → stopped | completed | errored
 *   any → disposed (terminal)
 */

export type RuntimeState =
  | 'uninitialized'
  | 'loaded'
  | 'starting'
  | 'running'
  | 'paused'
  | 'stopping'
  | 'stopped'
  | 'completed'
  | 'errored'
  | 'disposed';

export const RUNTIME_STATES: readonly RuntimeState[] = [
  'uninitialized',
  'loaded',
  'starting',
  'running',
  'paused',
  'stopping',
  'stopped',
  'completed',
  'errored',
  'disposed',
] as const;

export const TERMINAL_RUNTIME_STATES: readonly RuntimeState[] = [
  'stopped',
  'completed',
  'errored',
  'disposed',
] as const;

export const isRuntimeState = (value: unknown): value is RuntimeState =>
  typeof value === 'string' && (RUNTIME_STATES as readonly string[]).includes(value);

export const isTerminalRuntimeState = (state: RuntimeState): boolean =>
  (TERMINAL_RUNTIME_STATES as readonly RuntimeState[]).includes(state);
