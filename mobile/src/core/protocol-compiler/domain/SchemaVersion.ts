/**
 * Schema version — tracks the version of the protocol document format.
 *
 * Documents declare their schema via the `$schema` field. The compiler
 * uses this to determine which migration path to apply.
 */

import { AppError } from '@araflow/shared-contracts';

export const SUPPORTED_SCHEMA_VERSIONS = [
  'https://araflow.app/schemas/protocol/v1.json',
  'araflow://protocol/v1',
] as const;

export type SupportedSchemaUri = (typeof SUPPORTED_SCHEMA_VERSIONS)[number];

export const DEFAULT_SCHEMA_URI: SupportedSchemaUri =
  'https://araflow.app/schemas/protocol/v1.json';

export const isSupportedSchemaUri = (
  uri: unknown,
): uri is SupportedSchemaUri =>
  typeof uri === 'string' &&
  (SUPPORTED_SCHEMA_VERSIONS as readonly string[]).includes(uri);

/**
 * Compares two schema URIs and returns true if they refer to the same
 * major version of the protocol schema.
 */
export const isSchemaVersionCompatible = (
  candidate: string,
  base: SupportedSchemaUri,
): boolean => {
  const candidateMajor = extractMajor(candidate);
  const baseMajor = extractMajor(base);
  if (candidateMajor === null || baseMajor === null) return false;
  return candidateMajor === baseMajor;
};

const extractMajor = (uri: string): number | null => {
  const match = /\/v(\d+)(?:\.json)?$/.exec(uri);
  if (match === null) return null;
  const captured = match[1];
  if (captured === undefined) return null;
  const n = Number(captured);
  return Number.isInteger(n) ? n : null;
};

/**
 * Extracts the schema URI from a raw document. Returns null if absent.
 */
export const extractSchemaUri = (
  raw: unknown,
): string | null => {
  if (typeof raw !== 'object' || raw === null) return null;
  const schema = (raw as { $schema?: unknown }).$schema;
  return typeof schema === 'string' ? schema : null;
};

/**
 * Constructs a schema URI from a major version. Used during migration.
 */
export const buildSchemaUri = (major: number): string => {
  if (!Number.isInteger(major) || major < 1) {
    throw new AppError(`Invalid schema major version: ${major}`, {
      code: 'invalid_schema_version',
      severity: 'error',
      context: { major },
    });
  }
  return `https://araflow.app/schemas/protocol/v${major}.json`;
};

/**
 * Current schema major version — bump when the document shape changes
 * in a backward-incompatible way.
 */
export const CURRENT_SCHEMA_MAJOR = 1 as const;
