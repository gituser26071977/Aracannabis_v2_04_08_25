/**
 * events/lifecycle.ts — Canonical event types.
 *
 * Coverage:
 *   - Each event type has correct discriminator
 *   - All required fields present
 *   - CANONICAL_EVENT_TYPES is complete and matches events
 *   - CanonicalEvent is a discriminated union
 */

import {
  CANONICAL_EVENT_TYPES,
  type EngineStartedEvent,
  type EngineStoppedEvent,
  type EnginePausedEvent,
  type EngineResumedEvent,
  type TickEvent,
  type PhaseChangedEvent,
  type CycleCompletedEvent,
  type ProtocolLoadedEvent,
  type ProtocolCompiledEvent,
  type CanonicalEventType,
} from '../../src/events/lifecycle';
import { EngineId, ProtocolId } from '../../src/value-objects/ids';
import { SemanticVersion } from '../../src/value-objects/version';
import { Iso8601, Duration, CycleIndex } from '../../src/value-objects/numeric';

const ENGINE = EngineId('test-engine');
const PID = ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');
const VER = SemanticVersion('1.0.0');
const ISO = Iso8601('2024-01-15T10:30:00.000Z');
const DUR = Duration(1000);
const CI = CycleIndex(0);

describe('events/lifecycle', () => {
  it('CANONICAL_EVENT_TYPES contains the 9 expected types', () => {
    expect(CANONICAL_EVENT_TYPES).toEqual([
      'engine-started',
      'engine-stopped',
      'engine-paused',
      'engine-resumed',
      'tick',
      'phase-changed',
      'cycle-completed',
      'protocol-loaded',
      'protocol-compiled',
    ]);
  });

  it('EngineStartedEvent shape', () => {
    const e: EngineStartedEvent = {
      type: 'engine-started',
      monotonicMs: 0,
      engineId: ENGINE,
      startedAt: ISO,
    };
    expect(e.type).toBe('engine-started');
    expect(e.engineId).toBe(ENGINE);
    expect(e.startedAt).toBe(ISO);
  });

  it('EngineStoppedEvent shape', () => {
    const e: EngineStoppedEvent = {
      type: 'engine-stopped',
      monotonicMs: 0,
      engineId: ENGINE,
      stoppedAt: ISO,
      reason: 'completed',
    };
    expect(e.reason).toBe('completed');
  });

  it('EnginePausedEvent shape', () => {
    const e: EnginePausedEvent = {
      type: 'engine-paused',
      monotonicMs: 0,
      engineId: ENGINE,
      pausedAt: ISO,
      elapsedMs: 1000,
    };
    expect(e.elapsedMs).toBe(1000);
  });

  it('EngineResumedEvent shape', () => {
    const e: EngineResumedEvent = {
      type: 'engine-resumed',
      monotonicMs: 0,
      engineId: ENGINE,
      resumedAt: ISO,
      pausedForMs: 500,
    };
    expect(e.pausedForMs).toBe(500);
  });

  it('TickEvent shape', () => {
    const e: TickEvent = {
      type: 'tick',
      monotonicMs: 0,
      engineId: ENGINE,
      tickIndex: 42,
      elapsedMs: 4200,
    };
    expect(e.tickIndex).toBe(42);
  });

  it('PhaseChangedEvent shape', () => {
    const e: PhaseChangedEvent = {
      type: 'phase-changed',
      monotonicMs: 0,
      engineId: ENGINE,
      previousPhase: 'inhaling',
      currentPhase: 'holdAfterInhale',
      cycleIndex: CI,
      phaseProgress: 0.5,
    };
    expect(e.previousPhase).toBe('inhaling');
    expect(e.currentPhase).toBe('holdAfterInhale');
    expect(e.phaseProgress).toBe(0.5);
  });

  it('CycleCompletedEvent shape', () => {
    const e: CycleCompletedEvent = {
      type: 'cycle-completed',
      monotonicMs: 0,
      engineId: ENGINE,
      cycleIndex: CI,
      totalCycles: 10,
      cycleDuration: DUR,
    };
    expect(e.totalCycles).toBe(10);
  });

  it('ProtocolLoadedEvent shape', () => {
    const e: ProtocolLoadedEvent = {
      type: 'protocol-loaded',
      monotonicMs: 0,
      protocolId: PID,
      version: VER,
      loadedAt: ISO,
    };
    expect(e.protocolId).toBe(PID);
    expect(e.version).toBe(VER);
  });

  it('ProtocolCompiledEvent shape', () => {
    const e: ProtocolCompiledEvent = {
      type: 'protocol-compiled',
      monotonicMs: 0,
      protocolId: PID,
      version: VER,
      compiledAt: ISO,
      totalDuration: DUR,
    };
    expect(e.totalDuration).toBe(DUR);
  });

  it('CanonicalEventType is exhaustively covered', () => {
    const types: CanonicalEventType[] = [
      'engine-started',
      'engine-stopped',
      'engine-paused',
      'engine-resumed',
      'tick',
      'phase-changed',
      'cycle-completed',
      'protocol-loaded',
      'protocol-compiled',
    ];
    for (const t of types) {
      expect(CANONICAL_EVENT_TYPES).toContain(t);
    }
  });
});
