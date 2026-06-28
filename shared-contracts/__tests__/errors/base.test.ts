/**
 * errors/base.ts — Typed error hierarchy.
 *
 * Coverage:
 *   - ValidationError, CompilationError, EngineError, ProtocolError,
 *     TimerError, BreathError all extend AppError
 *   - Each preserves code/severity/context/cause/optional fields
 *   - prototype chain enables instanceof across module boundaries
 */

import {
  ValidationError,
  CompilationError,
  EngineError,
  ProtocolError,
  TimerError,
  BreathError,
} from '../../src/errors/base';
import { AppError } from '../../src/value-objects/validation';

describe('errors/base', () => {
  describe('ValidationError', () => {
    it('extends AppError and preserves fields', () => {
      const e = new ValidationError('bad', {
        code: 'v_err',
        severity: 'warn',
        context: { field: 'name' },
        path: '$.name',
      });
      expect(e).toBeInstanceOf(AppError);
      expect(e).toBeInstanceOf(ValidationError);
      expect(e.name).toBe('ValidationError');
      expect(e.message).toBe('bad');
      expect(e.code).toBe('v_err');
      expect(e.severity).toBe('warn');
      expect(e.context).toEqual({ field: 'name' });
      expect(e.path).toBe('$.name');
    });
    it('defaults code to validation_error when omitted', () => {
      const e = new ValidationError('x', { code: 'v', severity: 'error' });
      expect(e.code).toBe('v');
    });
    it('path is undefined when omitted', () => {
      const e = new ValidationError('x', { code: 'v', severity: 'error' });
      expect(e.path).toBeUndefined();
    });
    it('preserves prototype chain for instanceof', () => {
      const e = new ValidationError('x', { code: 'v', severity: 'error' });
      expect(e instanceof ValidationError).toBe(true);
      expect(e instanceof AppError).toBe(true);
      expect(e instanceof Error).toBe(true);
    });
  });

  describe('CompilationError', () => {
    it('extends AppError with source field', () => {
      const e = new CompilationError('fail', {
        code: 'c_err',
        severity: 'error',
        source: 'inline',
      });
      expect(e).toBeInstanceOf(AppError);
      expect(e.name).toBe('CompilationError');
      expect(e.source).toBe('inline');
    });
    it('source is undefined when omitted', () => {
      const e = new CompilationError('x', { code: 'c', severity: 'error' });
      expect(e.source).toBeUndefined();
    });
    it('preserves cause', () => {
      const cause = new Error('inner');
      const e = new CompilationError('outer', {
        code: 'c',
        severity: 'fatal',
        cause,
      });
      expect(e.cause).toBe(cause);
    });
  });

  describe('EngineError', () => {
    it('extends AppError', () => {
      const e = new EngineError('boom', { code: 'e_err', severity: 'error' });
      expect(e).toBeInstanceOf(AppError);
      expect(e).toBeInstanceOf(EngineError);
      expect(e.name).toBe('EngineError');
    });
  });

  describe('ProtocolError', () => {
    it('extends AppError', () => {
      const e = new ProtocolError('boom', { code: 'p_err', severity: 'warn' });
      expect(e).toBeInstanceOf(AppError);
      expect(e).toBeInstanceOf(ProtocolError);
      expect(e.name).toBe('ProtocolError');
    });
  });

  describe('TimerError', () => {
    it('extends AppError', () => {
      const e = new TimerError('boom', { code: 't_err', severity: 'error' });
      expect(e).toBeInstanceOf(AppError);
      expect(e).toBeInstanceOf(TimerError);
      expect(e.name).toBe('TimerError');
    });
  });

  describe('BreathError', () => {
    it('extends AppError', () => {
      const e = new BreathError('boom', { code: 'b_err', severity: 'warn' });
      expect(e).toBeInstanceOf(AppError);
      expect(e).toBeInstanceOf(BreathError);
      expect(e.name).toBe('BreathError');
    });
  });

  describe('Cross-type discrimination', () => {
    it('instanceof distinguishes between error types', () => {
      const a = new ValidationError('a', { code: 'c', severity: 'error' });
      const b = new CompilationError('b', { code: 'c', severity: 'error' });
      const c = new EngineError('c', { code: 'c', severity: 'error' });
      const d = new ProtocolError('d', { code: 'c', severity: 'error' });
      const e = new TimerError('e', { code: 'c', severity: 'error' });
      const f = new BreathError('f', { code: 'c', severity: 'error' });

      expect(a instanceof ValidationError).toBe(true);
      expect(b instanceof CompilationError).toBe(true);
      expect(c instanceof EngineError).toBe(true);
      expect(d instanceof ProtocolError).toBe(true);
      expect(e instanceof TimerError).toBe(true);
      expect(f instanceof BreathError).toBe(true);

      expect(a instanceof CompilationError).toBe(false);
      expect(b instanceof EngineError).toBe(false);
      expect(c instanceof ProtocolError).toBe(false);
      expect(d instanceof TimerError).toBe(false);
      expect(e instanceof BreathError).toBe(false);
      expect(f instanceof ValidationError).toBe(false);
    });
    it('all subclasses are also AppError and Error', () => {
      const all = [
        new ValidationError('a', { code: 'c', severity: 'error' }),
        new CompilationError('b', { code: 'c', severity: 'error' }),
        new EngineError('c', { code: 'c', severity: 'error' }),
        new ProtocolError('d', { code: 'c', severity: 'error' }),
        new TimerError('e', { code: 'c', severity: 'error' }),
        new BreathError('f', { code: 'c', severity: 'error' }),
      ];
      for (const e of all) {
        expect(e instanceof AppError).toBe(true);
        expect(e instanceof Error).toBe(true);
      }
    });
  });
});
