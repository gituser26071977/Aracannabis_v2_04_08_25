/**
 * Tests for AnimationEngineState — FSM type, predicates, and
 * legal transitions.
 */

import {
  ANIMATION_ENGINE_STATES,
  canAnimationEngineTransition,
  isAnimationEngineState,
  isTerminalAnimationEngineState,
  legalAnimationEngineTransitions,
} from '@core/animation-engine';

describe('AnimationEngineState — predicates', () => {
  it('accepts every state in the tuple', () => {
    for (const s of ANIMATION_ENGINE_STATES) {
      expect(isAnimationEngineState(s)).toBe(true);
    }
  });

  it('rejects unknown values', () => {
    expect(isAnimationEngineState('starting')).toBe(false);
    expect(isAnimationEngineState('')).toBe(false);
    expect(isAnimationEngineState(null)).toBe(false);
    expect(isAnimationEngineState(123)).toBe(false);
  });

  it('isTerminalAnimationEngineState is true only for disposed', () => {
    expect(isTerminalAnimationEngineState('disposed')).toBe(true);
    expect(isTerminalAnimationEngineState('idle')).toBe(false);
    expect(isTerminalAnimationEngineState('running')).toBe(false);
    expect(isTerminalAnimationEngineState('paused')).toBe(false);
  });
});

describe('AnimationEngineState — transitions', () => {
  it('idle can transition to running or disposed', () => {
    const next = legalAnimationEngineTransitions('idle');
    expect(next).toContain('running');
    expect(next).toContain('disposed');
  });

  it('running can transition to paused, idle, or disposed', () => {
    const next = legalAnimationEngineTransitions('running');
    expect(next).toContain('paused');
    expect(next).toContain('idle');
    expect(next).toContain('disposed');
  });

  it('paused can transition to running, idle, or disposed', () => {
    const next = legalAnimationEngineTransitions('paused');
    expect(next).toContain('running');
    expect(next).toContain('idle');
    expect(next).toContain('disposed');
  });

  it('disposed has no outgoing transitions', () => {
    expect(legalAnimationEngineTransitions('disposed')).toEqual([]);
  });

  it('canAnimationEngineTransition returns true only for legal moves', () => {
    expect(canAnimationEngineTransition('idle', 'running')).toBe(true);
    expect(canAnimationEngineTransition('idle', 'paused')).toBe(false);
    expect(canAnimationEngineTransition('running', 'running')).toBe(false);
    expect(canAnimationEngineTransition('running', 'idle')).toBe(true);
    expect(canAnimationEngineTransition('disposed', 'running')).toBe(false);
  });
});
