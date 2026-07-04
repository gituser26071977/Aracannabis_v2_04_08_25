/**
 * AraFlow — Build info resolver.
 *
 * Single source of truth for the values surfaced by the `/health`
 * endpoint:
 *
 *   - `version` — `process.env.ARAFLOW_VERSION` if set, otherwise the
 *     `version` field of `backend/package.json`. Falls back to `'0.0.0'`
 *     if neither resolves (should never happen in a packaged image).
 *
 *   - `commit` — `process.env.GIT_COMMIT` if set, otherwise the contents
 *     of `/app/COMMIT` (Dockerfile writes the build arg there), otherwise
 *     the literal string `'unknown'`.
 *
 *   - `build` — `process.env.BUILD_TIME` if set (expected as ISO-8601),
 *     otherwise the current `new Date().toISOString()`. This means an
 *     unparameterized run will report the process start time, which is
 *     fine for liveness; it is only authoritative when CI sets the env.
 *
 * Resolution is pure (no I/O at import time) and cached after the first
 * call so the `/health` handler does not re-read the filesystem on every
 * request.
 */

import * as fs from 'node:fs';
import { createRequire } from 'node:module';
import * as path from 'node:path';

// `import.meta.url` requires ESM. backend tsconfig uses CommonJS, so we
// resolve via `__filename` instead. In compiled output, `__filename` is
// provided by Node; in ts-node-dev, by the loader.
const requireFromHere = createRequire(__filename);

export interface BuildInfo {
  readonly version: string;
  readonly commit: string;
  readonly build: string;
}

const readPackageVersion = (): string => {
  try {
    // Resolve relative to this file so it works under `ts-node-dev`
    // (where `__dirname` points at the .ts source) and under `node`
    // (where it points at `dist/shared/health`).
    const pkgPath = path.resolve(__dirname, '..', '..', '..', 'package.json');
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const pkg = requireFromHere(pkgPath) as { version?: unknown };
    if (typeof pkg.version === 'string' && pkg.version.length > 0) {
      return pkg.version;
    }
    return '0.0.0';
  } catch {
    return '0.0.0';
  }
};

const readCommitFile = (): string => {
  try {
    const raw = fs.readFileSync('/app/COMMIT', 'utf8');
    const trimmed = raw.trim();
    if (trimmed.length > 0) {
      return trimmed;
    }
    return 'unknown';
  } catch {
    return 'unknown';
  }
};

let cached: BuildInfo | null = null;

export const getBuildInfo = (): BuildInfo => {
  if (cached !== null) {
    return cached;
  }
  const version = process.env['ARAFLOW_VERSION'] ?? readPackageVersion();
  const commit = process.env['GIT_COMMIT'] ?? readCommitFile();
  const build = process.env['BUILD_TIME'] ?? new Date().toISOString();
  cached = { version, commit, build };
  return cached;
};

/**
 * Test-only helper. Resets the module-level cache so subsequent calls to
 * `getBuildInfo()` re-read env / package / COMMIT file.
 */
export const __resetBuildInfoCacheForTests = (): void => {
  cached = null;
};
