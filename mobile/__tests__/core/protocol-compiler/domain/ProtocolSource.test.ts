/**
 * ProtocolSource — source factory and type guard tests.
 */

import {
  isProtocolSource,
  JsonSource,
} from '../../../../src/core/protocol-compiler/domain/ProtocolSource';

describe('ProtocolSource', () => {
  describe('JsonSource', () => {
    it('builds a source with format=json and raw', () => {
      const s = JsonSource('{}');
      expect(s.format).toBe('json');
      expect(s.raw).toBe('{}');
      expect(s.origin).toBeUndefined();
    });

    it('records origin when provided', () => {
      const s = JsonSource('{}', 'filesystem');
      expect(s.origin).toBe('filesystem');
    });
  });

  describe('isProtocolSource', () => {
    it('returns true for a JsonSource', () => {
      expect(isProtocolSource(JsonSource('{}'))).toBe(true);
    });

    it('returns false for null', () => {
      expect(isProtocolSource(null)).toBe(false);
    });

    it('returns false for non-objects', () => {
      expect(isProtocolSource('string')).toBe(false);
      expect(isProtocolSource(42)).toBe(false);
    });

    it('returns false when format is missing or wrong type', () => {
      expect(isProtocolSource({ raw: '{}' })).toBe(false);
      expect(isProtocolSource({ format: 1, raw: '{}' })).toBe(false);
    });

    it('returns false when raw is missing or wrong type', () => {
      expect(isProtocolSource({ format: 'json' })).toBe(false);
      expect(isProtocolSource({ format: 'json', raw: 1 })).toBe(false);
    });
  });
});