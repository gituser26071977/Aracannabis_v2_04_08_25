/**
 * SchemaVersion — URI compatibility and helpers.
 */

import {
  SUPPORTED_SCHEMA_VERSIONS,
  DEFAULT_SCHEMA_URI,
  CURRENT_SCHEMA_MAJOR,
  isSupportedSchemaUri,
  isSchemaVersionCompatible,
  extractSchemaUri,
  buildSchemaUri,
} from '../../../../src/core/protocol-compiler/domain/SchemaVersion';

describe('SchemaVersion', () => {
  describe('constants', () => {
    it('exposes two supported URIs', () => {
      expect(SUPPORTED_SCHEMA_VERSIONS.length).toBeGreaterThanOrEqual(2);
    });

    it('default URI points to v1', () => {
      expect(DEFAULT_SCHEMA_URI).toContain('v1');
    });

    it('current major is 1', () => {
      expect(CURRENT_SCHEMA_MAJOR).toBe(1);
    });
  });

  describe('isSupportedSchemaUri', () => {
    it('returns true for the default URI', () => {
      expect(isSupportedSchemaUri(DEFAULT_SCHEMA_URI)).toBe(true);
    });

    it('returns true for alternate v1 URI', () => {
      expect(isSupportedSchemaUri('araflow://protocol/v1')).toBe(true);
    });

    it('returns false for v2', () => {
      expect(isSupportedSchemaUri('https://araflow.app/schemas/protocol/v2.json')).toBe(false);
    });

    it('returns false for non-strings', () => {
      expect(isSupportedSchemaUri(42)).toBe(false);
      expect(isSupportedSchemaUri(null)).toBe(false);
    });
  });

  describe('isSchemaVersionCompatible', () => {
    it('returns true for matching v1 ↔ v1', () => {
      expect(isSchemaVersionCompatible(DEFAULT_SCHEMA_URI, DEFAULT_SCHEMA_URI)).toBe(true);
    });

    it('returns false for v1 vs v2', () => {
      expect(
        isSchemaVersionCompatible(
          'https://araflow.app/schemas/protocol/v2.json',
          DEFAULT_SCHEMA_URI,
        ),
      ).toBe(false);
    });

    it('returns false for malformed URIs', () => {
      expect(isSchemaVersionCompatible('not-a-uri', DEFAULT_SCHEMA_URI)).toBe(false);
    });
  });

  describe('extractSchemaUri', () => {
    it('returns the schema URI from a valid object', () => {
      expect(extractSchemaUri({ $schema: DEFAULT_SCHEMA_URI })).toBe(DEFAULT_SCHEMA_URI);
    });

    it('returns null when missing', () => {
      expect(extractSchemaUri({})).toBeNull();
    });

    it('returns null for non-string schema', () => {
      expect(extractSchemaUri({ $schema: 42 })).toBeNull();
    });

    it('returns null for non-objects', () => {
      expect(extractSchemaUri(null)).toBeNull();
      expect(extractSchemaUri('string')).toBeNull();
    });
  });

  describe('buildSchemaUri', () => {
    it('builds v1 URI', () => {
      expect(buildSchemaUri(1)).toBe('https://araflow.app/schemas/protocol/v1.json');
    });

    it('builds v2 URI', () => {
      expect(buildSchemaUri(2)).toBe('https://araflow.app/schemas/protocol/v2.json');
    });

    it('throws on 0', () => {
      expect(() => buildSchemaUri(0)).toThrow();
    });

    it('throws on negative', () => {
      expect(() => buildSchemaUri(-1)).toThrow();
    });

    it('throws on non-integer', () => {
      expect(() => buildSchemaUri(1.5)).toThrow();
    });
  });
});