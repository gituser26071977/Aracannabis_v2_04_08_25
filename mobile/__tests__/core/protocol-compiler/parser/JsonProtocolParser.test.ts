/**
 * JsonProtocolParser — end-to-end parsing tests.
 */

import { JsonProtocolParser } from '../../../../src/core/protocol-compiler/parser/JsonProtocolParser';
import { JsonSource } from '../../../../src/core/protocol-compiler/domain/ProtocolSource';
import {
  invalidJsonSource,
  validJsonSource,
} from '../fixtures';

describe('JsonProtocolParser', () => {
  const parser = new JsonProtocolParser();

  describe('capabilities', () => {
    it('reports format=json', () => {
      expect(parser.capabilities.format).toBe('json');
    });
  });

  describe('format mismatch', () => {
    it('returns ValidationError for non-json sources', () => {
      const result = parser.parse({ format: 'yaml' as never, raw: '' });
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.error.code).toBe('parser_format_mismatch');
      }
    });
  });

  describe('JSON parse errors', () => {
    it('returns ValidationError for malformed JSON', () => {
      const result = parser.parse(JsonSource(invalidJsonSource));
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.error.code).toBe('json_parse_error');
      }
    });
  });

  describe('structural validation', () => {
    it('rejects non-objects', () => {
      const result = parser.parse(JsonSource('"a string"'));
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.error.code).toBe('document_not_object');
      }
    });

    it('rejects missing fields', () => {
      const result = parser.parse(JsonSource(JSON.stringify({ $schema: 's' })));
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.error.code).toBe('document_missing_field');
      }
    });

    it('rejects empty id', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects empty version', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects empty title', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: '',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-object breath', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: 'not-object',
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-integer cycles', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1.5, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-array phases', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: 'not-array' },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects unknown phase type', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'unknown', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-integer duration', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1.5 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects unknown curve type', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000, curve: 'bouncy' }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects metadata that is not an object', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: 'not-object',
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects invalid evidence level', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { evidenceLevel: 'E' },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-array references', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { references: 'not-array' },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-array contraindications', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { contraindications: 42 },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-array tags', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { tags: 'oops' },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects non-string approvedAt', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { approvedAt: 42 },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });
  });

  describe('successful parsing', () => {
    it('parses a minimal valid document', () => {
      const result = parser.parse(JsonSource(validJsonSource));
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.value.title).toBe('JSON Source');
        expect(result.value.breath.phases).toHaveLength(2);
      }
    });

    it('parses full metadata', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01BRZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 'Full',
        description: 'desc',
        subtitle: 'sub',
        breath: {
          cycles: 2,
          restBetweenCyclesMs: 500,
          phases: [
            { type: 'inhale', durationMs: 1000, curve: 'ease-in' },
            { type: 'hold-in', durationMs: 1000 },
            { type: 'exhale', durationMs: 1000, curve: 'ease-out' },
          ],
        },
        metadata: {
          author: 'A',
          language: 'en',
          references: ['r1'],
          evidenceLevel: 'A',
          contraindications: ['c1'],
          category: 'calm',
          tags: ['t1'],
          approvedAt: '2026-01-01T00:00:00.000Z',
        },
        checksum: 'abc',
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.value.subtitle).toBe('sub');
        expect(result.value.description).toBe('desc');
        expect(result.value.checksum).toBe('abc');
        expect(result.value.metadata?.author).toBe('A');
        expect(result.value.breath.restBetweenCyclesMs).toBe(500);
      }
    });

    it('defaults $schema when not provided', () => {
      const json = JSON.stringify({
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(true);
      if (result.ok) {
        expect(result.value.$schema).toContain('v1');
      }
    });

    it('rejects invalid ULID id', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: 'not-a-ulid',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects invalid semver', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: 'not-semver',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });

    it('rejects invalid ISO 8601 in approvedAt', () => {
      const json = JSON.stringify({
        $schema: 'https://araflow.app/schemas/protocol/v1.json',
        id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
        version: '1.0.0',
        title: 't',
        breath: { cycles: 1, phases: [{ type: 'inhale', durationMs: 1000 }] },
        metadata: { approvedAt: 'not-iso' },
      });
      const result = parser.parse(JsonSource(json));
      expect(result.ok).toBe(false);
    });
  });
});