/**
 * interfaces/protocol.ts — ProtocolSource, ExecutionPlan, CompilerResult,
 * ValidationResult, Compiler.
 */

import type {
  ProtocolSource,
  ProtocolSourceLoader,
  ExecutionPlan,
  PhaseStep,
  CompilerResult,
  ValidationResult,
  Compiler,
} from '../../src/interfaces/protocol';
import { ProtocolId, EngineId } from '../../src/value-objects/ids';
import { SemanticVersion } from '../../src/value-objects/version';
import { Iso8601, Duration } from '../../src/value-objects/numeric';
import { Result, Ok, Err } from '../../src/patterns/result';
import { ValidationError, CompilationError } from '../../src/errors/base';

const PID = ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');
const VER = SemanticVersion('1.0.0');
const EID = EngineId('protocol-engine');
const ISO = Iso8601('2024-01-15T10:30:00.000Z');
const DUR = Duration(1000);

describe('interfaces/protocol', () => {
  describe('ProtocolSource', () => {
    it('accepts json source', () => {
      const src: ProtocolSource = { format: 'json', raw: '{}' };
      expect(src.format).toBe('json');
    });
    it('accepts source with optional fields', () => {
      const src: ProtocolSource = {
        format: 'markdown',
        raw: '# t',
        origin: 'https://example.com',
        fetchedAt: ISO,
      };
      expect(src.origin).toBe('https://example.com');
    });
  });

  describe('ProtocolSourceLoader', () => {
    it('accepts implementation', async () => {
      const loader: ProtocolSourceLoader = {
        load: async (_id, _v): Promise<Result<ProtocolSource, ValidationError>> =>
          Ok({ format: 'json', raw: '{}' }),
        loadFromString: (raw, format) => ({ format, raw }),
        available: () => [{ id: PID, version: VER }],
      };
      const r = await loader.load(PID, VER);
      expect(r.ok).toBe(true);
      expect(loader.available()).toHaveLength(1);
    });
    it('accepts error path', async () => {
      const loader: ProtocolSourceLoader = {
        load: async (): Promise<Result<ProtocolSource, ValidationError>> =>
          Err(new ValidationError('missing', { code: 'c', severity: 'warn' })),
        loadFromString: () => ({ format: 'json', raw: '' }),
        available: () => [],
      };
      const r = await loader.load(PID, VER);
      expect(r.ok).toBe(false);
    });
  });

  describe('ExecutionPlan', () => {
    it('accepts full plan', () => {
      const phases: PhaseStep[] = [
        { index: 0, phase: 'inhaling', duration: DUR, curve: 'linear' },
        { index: 1, phase: 'holdAfterInhale', duration: DUR, curve: 'linear' },
      ];
      const plan: ExecutionPlan = {
        protocolId: PID,
        version: VER,
        phases,
        totalDuration: DUR,
        cycles: 10,
        compiledAt: ISO,
        compiledBy: EID,
      };
      expect(plan.phases).toHaveLength(2);
      expect(plan.cycles).toBe(10);
    });
  });

  describe('CompilerResult / ValidationResult', () => {
    it('CompilerResult can carry plan and failures', () => {
      const r: CompilerResult = {
        plan: null,
        failures: [],
        warnings: [],
      };
      expect(r.plan).toBeNull();
    });
    it('ValidationResult expresses pass/fail', () => {
      const ok: ValidationResult = { valid: true, failures: [] };
      const fail: ValidationResult = { valid: false, failures: [] };
      expect(ok.valid).toBe(true);
      expect(fail.valid).toBe(false);
    });
  });

  describe('Compiler', () => {
    it('accepts implementation', () => {
      const c: Compiler = {
        compile: (_s): Result<CompilerResult, CompilationError> =>
          Ok({ plan: null, failures: [], warnings: [] }),
        validate: (_s): ValidationResult => ({ valid: true, failures: [] }),
      };
      const r = c.compile({ format: 'json', raw: '' });
      expect(r.ok).toBe(true);
      expect(c.validate({ format: 'json', raw: '' }).valid).toBe(true);
    });
    it('accepts error path', () => {
      const c: Compiler = {
        compile: (): Result<CompilerResult, CompilationError> =>
          Err(new CompilationError('boom', { code: 'c', severity: 'error' })),
        validate: () => ({ valid: false, failures: [] }),
      };
      const r = c.compile({ format: 'json', raw: '' });
      expect(r.ok).toBe(false);
    });
  });
});
