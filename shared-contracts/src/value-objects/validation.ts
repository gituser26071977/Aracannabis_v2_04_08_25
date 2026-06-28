/**
 * Validation helpers and base AppError for value-objects.
 *
 * These live in shared-contracts because value-objects need them, but
 * they are deliberately minimal — full error hierarchy lives in
 * `errors/`.
 */

export const ULID_PATTERN = /^[0-9A-HJKMNP-TV-Z]{26}$/;
export const ISO8601_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;
export const SEMVER_PATTERN = /^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$/;
export const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export const isNonEmptyString = (v: unknown): v is string =>
  typeof v === 'string' && v.length > 0;

export const isFiniteNumber = (v: unknown): v is number =>
  typeof v === 'number' && Number.isFinite(v);

export const isInteger = (v: unknown): v is number =>
  isFiniteNumber(v) && Number.isInteger(v);

export const isInRange = (v: number, min: number, max: number): boolean =>
  v >= min && v <= max;

export type AppErrorContext = Readonly<Record<string, unknown>>;

export interface AppErrorOptions {
  readonly code: string;
  readonly severity: 'info' | 'warn' | 'error' | 'fatal';
  readonly context?: AppErrorContext;
  readonly cause?: unknown;
}

export class AppError extends Error {
  public readonly code: string;
  public readonly severity: AppErrorOptions['severity'];
  public readonly context: AppErrorContext;
  public override readonly cause?: unknown;

  public constructor(message: string, options: AppErrorOptions) {
    super(message);
    this.name = 'AppError';
    this.code = options.code;
    this.severity = options.severity;
    this.context = options.context ?? {};
    if (options.cause !== undefined) {
      this.cause = options.cause;
    }
    Object.setPrototypeOf(this, AppError.prototype);
  }

  public toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      severity: this.severity,
      context: this.context,
      cause: this.cause instanceof Error ? this.cause.message : this.cause,
      stack: this.stack,
    };
  }
}