/**
 * ProtocolCompiler orchestrator end-to-end tests.
 */

import { ProtocolCompiler } from '../../../../src/core/protocol-compiler/compiler/ProtocolCompiler';
import { JsonSource } from '../../../../src/core/protocol-compiler/domain/ProtocolSource';
import { createMigrationRegistry } from '../../../../src/core/protocol-compiler/migration/ProtocolMigrationPipeline';
import { createParserRegistry } from '../../../../src/core/protocol-compiler/domain/ProtocolParser';
import { JsonProtocolParser } from '../../../../src/core/protocol-compiler/parser/JsonProtocolParser';
import { EngineId } from '@araflow/shared-contracts';

const COMPILER_ID = EngineId('protocol-compiler');

const makeCompiler = (): ProtocolCompiler =>
  new ProtocolCompiler({
    compiledBy: COMPILER_ID,
    now: () => 1_700_000_000_000,
  });

const validJson = (): string =>
  JSON.stringify({
    $schema: 'https://araflow.app/schemas/protocol/v1.json',
    id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    version: '1.0.0',
    title: 'Test',
    breath: {
      cycles: 2,
      phases: [
        { type: 'inhale', durationMs: 1000 },
        { type: 'exhale', durationMs: 1000 },
      ],
    },
  });

describe('ProtocolCompiler', () => {
  describe('successful compile', () => {
    it('produces a plan from a valid source', () => {
      const compiler = makeCompiler();
      const result = compiler.compile(JsonSource(validJson()));
      expect(result.failures).toEqual([]);
      expect(result.plan).not.toBeNull();
      if (result.plan) {
        expect(result.plan.cycles).toBe(2);
      }
    });

    it('records timings in diagnostics', () => {
      const compiler = makeCompiler();
      const result = compiler.compile(JsonSource(validJson()));
      expect(result.diagnostics.totalTimeMs).toBeGreaterThanOrEqual(0);
      expect(result.diagnostics.optimizerPasses.length).toBeGreaterThan(0);
    });

    it('emits lint warnings (not failures) for a document missing metadata', () => {
      const compiler = makeCompiler();
      const result = compiler.compile(JsonSource(validJson()));
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.plan).not.toBeNull();
    });
  });

  describe('compile failures', () => {
    it('fails when no parser is registered for the format', () => {
      const reg = createParserRegistry(); // empty
      const compiler = new ProtocolCompiler({
        compiledBy: COMPILER_ID,
        parsers: reg,
        now: () => 1_700_000_000_000,
      });
      const result = compiler.compile(JsonSource(validJson()));
      expect(result.failures.some((f) => f.code === 'parser_not_registered')).toBe(true);
      expect(result.plan).toBeNull();
    });

    it('fails when JSON is malformed', () => {
      const compiler = makeCompiler();
      const result = compiler.compile(JsonSource('not-json{'));
      expect(result.failures.some((f) => f.code === 'json_parse_error')).toBe(true);
      expect(result.plan).toBeNull();
    });

    it('fails on schema errors', () => {
      const compiler = makeCompiler();
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 'Empty phases',
        breath: { cycles: 1, phases: [] },
      });
      const result = compiler.compile(JsonSource(json));
      expect(result.failures.length).toBeGreaterThan(0);
      expect(result.plan).toBeNull();
    });

    it('fails on semantic errors (no exhale)', () => {
      const compiler = makeCompiler();
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 'No exhale',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = compiler.compile(JsonSource(json));
      expect(result.failures.some((f) => f.code === 'semantic_no_exhale')).toBe(true);
    });

    it('fails on version incompatibility', () => {
      const compiler = new ProtocolCompiler({
        compiledBy: COMPILER_ID,
        compatibilityMajor: 1,
        now: () => 1_700_000_000_000,
      });
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '5.0.0',
        title: 'Future',
        breath: {
          cycles: 1,
          phases: [
            { type: 'inhale', durationMs: 1000 },
            { type: 'exhale', durationMs: 1000 },
          ],
        },
      });
      const result = compiler.compile(JsonSource(json));
      expect(result.failures.some((f) => f.code === 'compat_future_major')).toBe(true);
    });
  });

  describe('deterministic output', () => {
    it('produces identical checksums for identical inputs', () => {
      const a = makeCompiler().compile(JsonSource(validJson()));
      const b = makeCompiler().compile(JsonSource(validJson()));
      expect(a.plan?.checksum).toBe(b.plan?.checksum);
    });

    it('produces identical executionIds for identical inputs', () => {
      const a = makeCompiler().compile(JsonSource(validJson()));
      const b = makeCompiler().compile(JsonSource(validJson()));
      expect(a.plan?.executionId).toBe(b.plan?.executionId);
    });
  });

  describe('config injection', () => {
    it('accepts custom parsers and migrations', () => {
      const parsers = createParserRegistry();
      parsers.register(new JsonProtocolParser());
      const migrations = createMigrationRegistry();
      const compiler = new ProtocolCompiler({
        compiledBy: COMPILER_ID,
        parsers,
        migrations,
        now: () => 1_700_000_000_000,
      });
      const result = compiler.compile(JsonSource(validJson()));
      expect(result.plan).not.toBeNull();
    });

    it('respects custom compatibilityMajor', () => {
      const compiler = new ProtocolCompiler({
        compiledBy: COMPILER_ID,
        compatibilityMajor: 1,
        now: () => 1_700_000_000_000,
      });
      const result = compiler.compile(JsonSource(validJson()));
      // Filter to blocking failures only.
      const blocking = result.failures.filter(
        (f) => f.severity === 'error' || f.severity === 'fatal',
      );
      expect(blocking).toEqual([]);
    });
  });
});