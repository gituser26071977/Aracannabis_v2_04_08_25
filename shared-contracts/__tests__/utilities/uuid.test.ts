/**
 * uuid.ts — UUID v4 generation + validation.
 */

import {
  generateUuidV4,
  validateUuidV4,
  generateUlidLike,
} from '../../src/utilities/uuid';
import { UUID_V4_PATTERN, ULID_PATTERN } from '../../src/value-objects/validation';

describe('utilities/uuid', () => {
  describe('generateUuidV4', () => {
    it('produces a valid v4 UUID', () => {
      const id = generateUuidV4();
      expect(UUID_V4_PATTERN.test(id)).toBe(true);
    });
    it('produces unique IDs across many calls', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 1000; i += 1) {
        ids.add(generateUuidV4());
      }
      expect(ids.size).toBe(1000);
    });
    it('has version nibble = 4', () => {
      const id = generateUuidV4();
      expect(id[14]).toBe('4');
    });
    it('has variant 10xx in the 17th position', () => {
      const id = generateUuidV4();
      const c = id[19];
      expect(['8', '9', 'a', 'b']).toContain(c?.toLowerCase());
    });
  });

  describe('validateUuidV4', () => {
    it('accepts valid UUID', () => {
      expect(() => validateUuidV4('REDACTED')).not.toThrow();
    });
    it('rejects invalid', () => {
      expect(() => validateUuidV4('not-a-uuid')).toThrow(/Invalid UUID v4/);
      expect(() => validateUuidV4('')).toThrow(/Invalid UUID v4/);
    });
  });

  describe('generateUlidLike', () => {
    it('produces a 26-char ULID-like string', () => {
      const ulid = generateUlidLike();
      expect(ulid).toHaveLength(26);
      expect(ULID_PATTERN.test(ulid)).toBe(true);
    });
    it('encodes timestamp prefix', () => {
      const ts = 1700000000000;
      const ulid = generateUlidLike(ts);
      // First 10 chars represent timestamp — re-derive to confirm
      const CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
      let derived = 0;
      for (let i = 0; i < 10; i += 1) {
        const ch = ulid[i];
        const idx = CROCKFORD.indexOf(ch ?? '0');
        derived = derived * 32 + idx;
      }
      expect(derived).toBe(ts);
    });
    it('uses provided timestamp', () => {
      const ulid1 = generateUlidLike(1000);
      const ulid2 = generateUlidLike(2000);
      expect(ulid1 < ulid2).toBe(true); // lexicographically sortable
    });
    it('defaults to Date.now', () => {
      const ulid = generateUlidLike();
      expect(ulid).toHaveLength(26);
    });
  });
});
