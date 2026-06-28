/**
 * SemanticVersion — semantic version "MAJOR.MINOR.PATCH" with optional
 * pre-release and build metadata.
 *
 * Format: `^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$`
 *
 * Comparison rules follow semver.org:
 *   - Major > Minor > Patch in priority.
 *   - Pre-release versions have lower precedence than the normal version.
 *   - Identifiers compared lexically; numeric identifiers compared numerically.
 *   - Build metadata is ignored in comparison.
 */

import { AppError, SEMVER_PATTERN, isNonEmptyString } from './validation';
import type { Brand } from './ids';

export type SemanticVersion = Brand<string, 'SemanticVersion'>;

export interface ParsedVersion {
  readonly major: number;
  readonly minor: number;
  readonly patch: number;
  readonly prerelease: readonly string[];
  readonly build: readonly string[];
}

const compareIdentifiers = (a: string, b: string): number => {
  const aIsNum = /^\d+$/.test(a);
  const bIsNum = /^\d+$/.test(b);
  if (aIsNum && bIsNum) {
    return Number(a) - Number(b);
  }
  if (aIsNum) return -1; // numeric < non-numeric
  if (bIsNum) return 1;
  return a.localeCompare(b);
};

/**
 * Constructs a SemanticVersion from a string. Throws on invalid format.
 */
export const SemanticVersion = (raw: string): SemanticVersion => {
  if (!isNonEmptyString(raw) || !SEMVER_PATTERN.test(raw)) {
    throw new AppError(
      `Invalid SemanticVersion: must match semver pattern, got "${raw}"`,
      {
        code: 'invalid_semantic_version',
        severity: 'warn',
        context: { raw },
      },
    );
  }
  return raw as SemanticVersion;
};

/**
 * Parses a SemanticVersion into its components.
 */
export const parseSemanticVersion = (v: SemanticVersion): ParsedVersion => {
  const raw = v as string;
  const [mainPart, buildPart] = raw.split('+');
  // Regex ensures mainPart matches \d+\.\d+\.\d+ — three numeric segments.
  const split = (buildPart !== undefined ? mainPart : raw).split('-');
  const versionPart = split[0]!;
  const prereleasePart = split.slice(1).join('-');
  const parts = versionPart.split('.');
  const major = Number(parts[0]);
  const minor = Number(parts[1]);
  const patch = Number(parts[2]);
  const prerelease = prereleasePart !== '' ? prereleasePart.split('.') : [];
  const build = buildPart !== undefined ? buildPart.split('.') : [];
  return { major, minor, patch, prerelease, build };
};

/**
 * Compares two SemanticVersions.
 * Returns -1 if a < b, 0 if equal, 1 if a > b.
 */
export const compareSemanticVersions = (
  a: SemanticVersion,
  b: SemanticVersion,
): number => {
  const pa = parseSemanticVersion(a);
  const pb = parseSemanticVersion(b);

  if (pa.major !== pb.major) return pa.major < pb.major ? -1 : 1;
  if (pa.minor !== pb.minor) return pa.minor < pb.minor ? -1 : 1;
  if (pa.patch !== pb.patch) return pa.patch < pb.patch ? -1 : 1;

  // Pre-release has lower precedence than no pre-release.
  if (pa.prerelease.length === 0 && pb.prerelease.length === 0) return 0;
  if (pa.prerelease.length === 0) return 1;
  if (pb.prerelease.length === 0) return -1;

  // Compare pre-release identifiers.
  const len = Math.min(pa.prerelease.length, pb.prerelease.length);
  for (let i = 0; i < len; i += 1) {
    const paId = pa.prerelease[i];
    const pbId = pb.prerelease[i];
    if (paId !== undefined && pbId !== undefined) {
      const cmp = compareIdentifiers(paId, pbId);
      if (cmp !== 0) return cmp < 0 ? -1 : 1;
    }
  }
  return pa.prerelease.length - pb.prerelease.length < 0 ? -1 : 1;
};

export const isVersionCompatible = (
  base: SemanticVersion,
  candidate: SemanticVersion,
): boolean => compareSemanticVersions(candidate, base) >= 0;