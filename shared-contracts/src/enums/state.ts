/**
 * State enums — canonical state values for engines, protocols, sessions.
 *
 * Convention: each enum is a `const` tuple of string literals, with both
 * a type alias and a runtime constant array. This gives:
 *   - Type safety in conditionals
 *   - Runtime iteration
 *   - Easy serialization
 *
 * IMPORTANT: These are the CANONICAL enums for shared use across all
 * engines. Engines may have additional internal states but MUST expose
 * these for cross-engine communication.
 */

// =============================================================================
// EngineState
// =============================================================================

/**
 * Lifecycle states shared by all engines (timer, breath, protocol, etc.).
 */
export const ENGINE_STATES = [
  'idle',
  'initializing',
  'ready',
  'running',
  'paused',
  'stopping',
  'stopped',
  'errored',
  'disposed',
] as const;

export type EngineState = (typeof ENGINE_STATES)[number];

export const isEngineState = (v: unknown): v is EngineState =>
  typeof v === 'string' && (ENGINE_STATES as readonly string[]).includes(v);

// =============================================================================
// ProtocolState
// =============================================================================

export const PROTOCOL_STATES = [
  'unloaded',
  'loading',
  'loaded',
  'compiling',
  'compiled',
  'invalid',
] as const;

export type ProtocolState = (typeof PROTOCOL_STATES)[number];

export const isProtocolState = (v: unknown): v is ProtocolState =>
  typeof v === 'string' && (PROTOCOL_STATES as readonly string[]).includes(v);

// =============================================================================
// SessionState
// =============================================================================

export const SESSION_STATES = [
  'idle',
  'preparing',
  'active',
  'paused',
  'completed',
  'cancelled',
  'interrupted',
  'errored',
] as const;

export type SessionState = (typeof SESSION_STATES)[number];

export const isSessionState = (v: unknown): v is SessionState =>
  typeof v === 'string' && (SESSION_STATES as readonly string[]).includes(v);