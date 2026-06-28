/**
 * version.ts — SemanticVersion + parsing + comparison.
 *
 * Coverage:
 *   - SemanticVersion constructor (accepts/rejects)
 *   - parseSemanticVersion (all components)
 *   - compareSemanticVersions (all comparison paths)
 *   - isVersionCompatible
 */

import {
  SemanticVersion,
  parseSemanticVersion,
  compareSemanticVersions,
  isVersionCompatible,
} from '../../src/value-objects/version';

describe('value-objects/version', () => {
  describe('SemanticVersion constructor', () => {
    it('accepts valid semver', () => {
      expect(SemanticVersion('1.2.3')).toBe('1.2.3');
      expect(SemanticVersion('1.0.0-alpha')).toBe('1.0.0-alpha');
      expect(SemanticVersion('1.0.0-alpha.1')).toBe('1.0.0-alpha.1');
      expect(SemanticVersion('1.0.0+build.1')).toBe('1.0.0+build.1');
      expect(SemanticVersion('1.0.0-beta.2+exp.sha.5114f85')).toBe('1.0.0-beta.2+exp.sha.5114f85');
    });
    it('rejects empty string', () => {
      expect(() => SemanticVersion('')).toThrow(/Invalid SemanticVersion/);
    });
    it('rejects invalid format', () => {
      expect(() => SemanticVersion('1')).toThrow(/Invalid SemanticVersion/);
      expect(() => SemanticVersion('1.0')).toThrow(/Invalid SemanticVersion/);
      expect(() => SemanticVersion('v1.0.0')).toThrow(/Invalid SemanticVersion/);
      expect(() => SemanticVersion('not-a-version')).toThrow(/Invalid SemanticVersion/);
    });
    it('error code is invalid_semantic_version', () => {
      try {
        SemanticVersion('bad');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_semantic_version');
      }
    });
  });

  describe('parseSemanticVersion', () => {
    it('parses plain MAJOR.MINOR.PATCH', () => {
      const parsed = parseSemanticVersion(SemanticVersion('1.2.3'));
      expect(parsed.major).toBe(1);
      expect(parsed.minor).toBe(2);
      expect(parsed.patch).toBe(3);
      expect(parsed.prerelease).toEqual([]);
      expect(parsed.build).toEqual([]);
    });
    it('parses prerelease', () => {
      const parsed = parseSemanticVersion(SemanticVersion('1.0.0-alpha.1'));
      expect(parsed.major).toBe(1);
      expect(parsed.minor).toBe(0);
      expect(parsed.patch).toBe(0);
      expect(parsed.prerelease).toEqual(['alpha', '1']);
      expect(parsed.build).toEqual([]);
    });
    it('parses build metadata', () => {
      const parsed = parseSemanticVersion(SemanticVersion('1.0.0+build.1'));
      expect(parsed.prerelease).toEqual([]);
      expect(parsed.build).toEqual(['build', '1']);
    });
    it('parses prerelease + build', () => {
      const parsed = parseSemanticVersion(SemanticVersion('1.0.0-rc.1+build.42'));
      expect(parsed.prerelease).toEqual(['rc', '1']);
      expect(parsed.build).toEqual(['build', '42']);
    });
  });

  describe('compareSemanticVersions', () => {
    it('returns 0 for equal versions', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0'), SemanticVersion('1.0.0'))).toBe(0);
      expect(compareSemanticVersions(SemanticVersion('1.0.0+a'), SemanticVersion('1.0.0+b'))).toBe(0);
    });
    it('major differs → major wins', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0'), SemanticVersion('2.0.0'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('2.0.0'), SemanticVersion('1.0.0'))).toBe(1);
    });
    it('minor differs → minor wins', () => {
      expect(compareSemanticVersions(SemanticVersion('1.1.0'), SemanticVersion('1.2.0'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.3.0'), SemanticVersion('1.2.0'))).toBe(1);
    });
    it('patch differs → patch wins', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.1'), SemanticVersion('1.0.2'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.0.3'), SemanticVersion('1.0.2'))).toBe(1);
    });
    it('prerelease has lower precedence than release', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha'), SemanticVersion('1.0.0'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.0.0'), SemanticVersion('1.0.0-alpha'))).toBe(1);
    });
    it('prerelease identifiers compared lexically', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha'), SemanticVersion('1.0.0-beta'))).toBe(-1);
    });
    it('numeric prerelease identifiers compared numerically', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha.1'), SemanticVersion('1.0.0-alpha.2'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha.10'), SemanticVersion('1.0.0-alpha.2'))).toBe(1);
    });
    it('numeric identifier < non-numeric identifier', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0-1'), SemanticVersion('1.0.0-alpha'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha'), SemanticVersion('1.0.0-1'))).toBe(1);
    });
    it('longer prerelease wins when prefix matches', () => {
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha'), SemanticVersion('1.0.0-alpha.1'))).toBe(-1);
      expect(compareSemanticVersions(SemanticVersion('1.0.0-alpha.1'), SemanticVersion('1.0.0-alpha'))).toBe(1);
    });
  });

  describe('isVersionCompatible', () => {
    it('returns true when candidate >= base', () => {
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('1.0.0'))).toBe(true);
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('1.0.1'))).toBe(true);
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('1.1.0'))).toBe(true);
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('2.0.0'))).toBe(true);
    });
    it('returns false when candidate < base', () => {
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('0.9.9'))).toBe(false);
      expect(isVersionCompatible(SemanticVersion('2.0.0'), SemanticVersion('1.99.99'))).toBe(false);
    });
    it('prerelease counts as lower than release', () => {
      expect(isVersionCompatible(SemanticVersion('1.0.0'), SemanticVersion('1.0.0-alpha'))).toBe(false);
      expect(isVersionCompatible(SemanticVersion('1.0.0-alpha'), SemanticVersion('1.0.0'))).toBe(true);
    });
  });
});
