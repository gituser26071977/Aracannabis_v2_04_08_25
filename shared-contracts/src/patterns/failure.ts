/**
 * Failure — structured failure type for compilation/validation results.
 *
 * Used by ValidationResult and CompilerResult to communicate multiple
 * issues at once (instead of failing on the first error).
 */

import type { Severity } from '../enums/priority';

export interface Failure {
  readonly code: string;
  readonly message: string;
  readonly severity: Severity;
  readonly path?: string;
  readonly context?: Readonly<Record<string, unknown>>;
}

export const Failure = (params: {
  readonly code: string;
  readonly message: string;
  readonly severity: Severity;
  readonly path?: string;
  readonly context?: Readonly<Record<string, unknown>>;
}): Failure => {
  const base: Failure = {
    code: params.code,
    message: params.message,
    severity: params.severity,
  };
  return Object.freeze({
    ...base,
    ...(params.path !== undefined ? { path: params.path } : {}),
    ...(params.context !== undefined ? { context: params.context } : {}),
  });
};

export const isFailure = (v: unknown): v is Failure =>
  typeof v === 'object' && v !== null &&
  typeof (v as Failure).code === 'string' &&
  typeof (v as Failure).message === 'string' &&
  typeof (v as Failure).severity === 'string';

/**
 * Groups failures by severity. Returns a frozen record.
 */
export const groupFailuresBySeverity = (
  failures: readonly Failure[],
): Readonly<Record<Severity, readonly Failure[]>> => {
  const grouped: Record<Severity, Failure[]> = {
    info: [],
    warn: [],
    error: [],
    fatal: [],
  };
  for (const f of failures) {
    grouped[f.severity].push(f);
  }
  return Object.freeze({
    info: Object.freeze(grouped.info),
    warn: Object.freeze(grouped.warn),
    error: Object.freeze(grouped.error),
    fatal: Object.freeze(grouped.fatal),
  });
};

/**
 * Returns true if any failure is at error or fatal severity.
 */
export const hasBlockingFailures = (failures: readonly Failure[]): boolean =>
  failures.some((f) => f.severity === 'error' || f.severity === 'fatal');