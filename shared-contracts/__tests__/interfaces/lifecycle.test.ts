/**
 * interfaces/lifecycle.ts — Disposable, Subscription, Engine, LifecycleController.
 *
 * Coverage:
 *   - Type-level conformance of a sample implementation.
 *   - Compile-time only; runtime behavior verified via shape assertions.
 */

import type {
  Disposable,
  Subscription,
  Engine,
  LifecycleController,
} from '../../src/interfaces/lifecycle';
import type { EngineId } from '../../src/value-objects/ids';
import type { EngineState } from '../../src/enums/state';
import type { Result } from '../../src/patterns/result';
import type { EngineError } from '../../src/errors/base';

describe('interfaces/lifecycle', () => {
  describe('Disposable', () => {
    it('accepts implementations', () => {
      const d: Disposable = {
        dispose: () => undefined,
        disposed: false,
      };
      d.dispose();
      expect(d.disposed).toBe(false); // implementation decides
    });
    it('accepts readonly disposed', () => {
      const d: Disposable = {
        dispose: () => undefined,
        get disposed() {
          return true;
        },
      };
      expect(d.disposed).toBe(true);
    });
  });

  describe('Subscription', () => {
    it('accepts implementations', () => {
      let active = true;
      const s: Subscription = {
        unsubscribe: () => {
          active = false;
        },
        get active() {
          return active;
        },
      };
      expect(s.active).toBe(true);
      s.unsubscribe();
      expect(s.active).toBe(false);
    });
  });

  describe('Engine', () => {
    it('accepts a sample engine', () => {
      const id = 'sample-engine' as EngineId;
      const state: EngineState = 'idle';
      const engine: Engine = {
        id,
        state,
        snapshot: () => ({ id, state }),
        subscribe: () => ({
          unsubscribe: () => undefined,
          active: true,
        }),
        dispose: () => undefined,
      };
      expect(engine.id).toBe(id);
      expect(engine.state).toBe('idle');
      expect(engine.snapshot()).toEqual({ id, state });
    });
  });

  describe('LifecycleController', () => {
    it('accepts a sample controller', () => {
      const controller: LifecycleController = {
        start: (): Result<void, EngineError> => ({ ok: true, value: undefined }),
        pause: (): Result<void, EngineError> => ({ ok: true, value: undefined }),
        resume: (): Result<void, EngineError> => ({ ok: true, value: undefined }),
        stop: (): Result<void, EngineError> => ({ ok: true, value: undefined }),
      };
      expect(controller.start().ok).toBe(true);
      expect(controller.pause().ok).toBe(true);
      expect(controller.resume().ok).toBe(true);
      expect(controller.stop().ok).toBe(true);
    });
  });
});
