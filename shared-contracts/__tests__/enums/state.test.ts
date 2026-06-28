/**
 * state.ts — EngineState, ProtocolState, SessionState enums.
 *
 * Coverage:
 *   - Tuples contain expected values
 *   - Type alias matches tuple
 *   - isX predicates
 */

import {
  ENGINE_STATES,
  isEngineState,
  PROTOCOL_STATES,
  isProtocolState,
  SESSION_STATES,
  isSessionState,
} from '../../src/enums/state';

describe('enums/state', () => {
  describe('ENGINE_STATES', () => {
    it('contains canonical states', () => {
      expect(ENGINE_STATES).toEqual([
        'idle',
        'initializing',
        'ready',
        'running',
        'paused',
        'stopping',
        'stopped',
        'errored',
        'disposed',
      ]);
    });
    it('isEngineState accepts valid', () => {
      expect(isEngineState('idle')).toBe(true);
      expect(isEngineState('running')).toBe(true);
      expect(isEngineState('disposed')).toBe(true);
    });
    it('isEngineState rejects invalid', () => {
      expect(isEngineState('unknown')).toBe(false);
      expect(isEngineState('')).toBe(false);
      expect(isEngineState(null)).toBe(false);
      expect(isEngineState(undefined)).toBe(false);
      expect(isEngineState(42)).toBe(false);
    });
  });

  describe('PROTOCOL_STATES', () => {
    it('contains canonical states', () => {
      expect(PROTOCOL_STATES).toEqual([
        'unloaded',
        'loading',
        'loaded',
        'compiling',
        'compiled',
        'invalid',
      ]);
    });
    it('isProtocolState accepts valid', () => {
      expect(isProtocolState('loaded')).toBe(true);
      expect(isProtocolState('invalid')).toBe(true);
    });
    it('isProtocolState rejects invalid', () => {
      expect(isProtocolState('whatever')).toBe(false);
      expect(isProtocolState(null)).toBe(false);
    });
  });

  describe('SESSION_STATES', () => {
    it('contains canonical states', () => {
      expect(SESSION_STATES).toEqual([
        'idle',
        'preparing',
        'active',
        'paused',
        'completed',
        'cancelled',
        'interrupted',
        'errored',
      ]);
    });
    it('isSessionState accepts valid', () => {
      expect(isSessionState('active')).toBe(true);
      expect(isSessionState('errored')).toBe(true);
    });
    it('isSessionState rejects invalid', () => {
      expect(isSessionState('done')).toBe(false);
      expect(isSessionState(undefined)).toBe(false);
    });
  });
});
