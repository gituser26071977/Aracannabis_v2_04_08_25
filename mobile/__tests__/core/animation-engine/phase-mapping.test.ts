/**
 * Tests for phase-mapping utility.
 */

import { mapBreathPhase, mapRuntimeState, mapSessionState } from '@core/animation-engine';

describe('mapBreathPhase', () => {
  it("'inhaling' maps to animation=inhale, hold=none", () => {
    expect(mapBreathPhase('inhaling')).toEqual({ animation: 'inhale', hold: 'none' });
  });
  it("'holdAfterInhale' maps to animation=hold, hold=peak", () => {
    expect(mapBreathPhase('holdAfterInhale')).toEqual({ animation: 'hold', hold: 'peak' });
  });
  it("'exhaling' maps to animation=exhale, hold=none", () => {
    expect(mapBreathPhase('exhaling')).toEqual({ animation: 'exhale', hold: 'none' });
  });
  it("'holdAfterExhale' maps to animation=hold, hold=trough", () => {
    expect(mapBreathPhase('holdAfterExhale')).toEqual({ animation: 'hold', hold: 'trough' });
  });
});

describe('mapSessionState', () => {
  it("'idle' → 'idle'", () => expect(mapSessionState('idle')).toBe('idle'));
  it("'preparing' → 'preparing'", () => expect(mapSessionState('preparing')).toBe('preparing'));
  it("'completed' → 'completed'", () => expect(mapSessionState('completed')).toBe('completed'));
  it("'cancelled' → 'idle'", () => expect(mapSessionState('cancelled')).toBe('idle'));
  it("'failed' → 'idle'", () => expect(mapSessionState('failed')).toBe('idle'));
  it("'running' → 'idle' (engine decides animation phase via events)", () =>
    expect(mapSessionState('running')).toBe('idle'));
});

describe('mapRuntimeState', () => {
  it("'uninitialized' → 'idle'", () => expect(mapRuntimeState('uninitialized')).toBe('idle'));
  it("'starting' → 'preparing'", () => expect(mapRuntimeState('starting')).toBe('preparing'));
  it("'completed' → 'completed'", () => expect(mapRuntimeState('completed')).toBe('completed'));
  it("'errored' → 'idle'", () => expect(mapRuntimeState('errored')).toBe('idle'));
});
