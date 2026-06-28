/**
 * Canonical events — EngineStarted, EngineStopped, EnginePaused,
 * EngineResumed, Tick, PhaseChanged, CycleCompleted, ProtocolLoaded,
 * ProtocolCompiled.
 *
 * All events share the base shape from observability.Event. Engine-
 * specific events add typed payload fields.
 */

import type { EngineId } from '../value-objects/ids';
import type { ProtocolId } from '../value-objects/ids';
import type { SemanticVersion } from '../value-objects/version';
import type { Iso8601, Duration, CycleIndex } from '../value-objects/numeric';
import type { BreathPhase } from '../enums/breath';
import type { Event } from '../interfaces/observability';

// =============================================================================
// EngineStarted
// =============================================================================

export interface EngineStartedEvent extends Event {
  readonly type: 'engine-started';
  readonly engineId: EngineId;
  readonly startedAt: Iso8601;
}

// =============================================================================
// EngineStopped
// =============================================================================

export interface EngineStoppedEvent extends Event {
  readonly type: 'engine-stopped';
  readonly engineId: EngineId;
  readonly stoppedAt: Iso8601;
  readonly reason: 'completed' | 'cancelled' | 'errored';
}

// =============================================================================
// EnginePaused
// =============================================================================

export interface EnginePausedEvent extends Event {
  readonly type: 'engine-paused';
  readonly engineId: EngineId;
  readonly pausedAt: Iso8601;
  readonly elapsedMs: number;
}

// =============================================================================
// EngineResumed
// =============================================================================

export interface EngineResumedEvent extends Event {
  readonly type: 'engine-resumed';
  readonly engineId: EngineId;
  readonly resumedAt: Iso8601;
  readonly pausedForMs: number;
}

// =============================================================================
// Tick
// =============================================================================

export interface TickEvent extends Event {
  readonly type: 'tick';
  readonly engineId: EngineId;
  readonly tickIndex: number;
  readonly elapsedMs: number;
}

// =============================================================================
// PhaseChanged
// =============================================================================

export interface PhaseChangedEvent extends Event {
  readonly type: 'phase-changed';
  readonly engineId: EngineId;
  readonly previousPhase: BreathPhase | null;
  readonly currentPhase: BreathPhase;
  readonly cycleIndex: CycleIndex;
  readonly phaseProgress: number;
}

// =============================================================================
// CycleCompleted
// =============================================================================

export interface CycleCompletedEvent extends Event {
  readonly type: 'cycle-completed';
  readonly engineId: EngineId;
  readonly cycleIndex: CycleIndex;
  readonly totalCycles: number;
  readonly cycleDuration: Duration;
}

// =============================================================================
// ProtocolLoaded
// =============================================================================

export interface ProtocolLoadedEvent extends Event {
  readonly type: 'protocol-loaded';
  readonly protocolId: ProtocolId;
  readonly version: SemanticVersion;
  readonly loadedAt: Iso8601;
}

// =============================================================================
// ProtocolCompiled
// =============================================================================

export interface ProtocolCompiledEvent extends Event {
  readonly type: 'protocol-compiled';
  readonly protocolId: ProtocolId;
  readonly version: SemanticVersion;
  readonly compiledAt: Iso8601;
  readonly totalDuration: Duration;
}

/**
 * Union of all canonical events.
 */
export type CanonicalEvent =
  | EngineStartedEvent
  | EngineStoppedEvent
  | EnginePausedEvent
  | EngineResumedEvent
  | TickEvent
  | PhaseChangedEvent
  | CycleCompletedEvent
  | ProtocolLoadedEvent
  | ProtocolCompiledEvent;

export const CANONICAL_EVENT_TYPES = [
  'engine-started',
  'engine-stopped',
  'engine-paused',
  'engine-resumed',
  'tick',
  'phase-changed',
  'cycle-completed',
  'protocol-loaded',
  'protocol-compiled',
] as const;

export type CanonicalEventType = (typeof CANONICAL_EVENT_TYPES)[number];