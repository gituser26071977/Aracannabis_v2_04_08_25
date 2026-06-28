/**
 * Base error types — typed error hierarchy.
 *
 * All errors extend `AppError` (defined in value-objects/validation.ts)
 * to maintain a consistent shape: name, code, severity, context, cause.
 *
 * Use specific error classes for type-based pattern matching via
 * `instanceof`. Use `code` for string-based matching across boundaries
 * (IPC, serialization, logs).
 */

import { AppError, type AppErrorOptions } from '../value-objects/validation';

export type {
  AppErrorContext,
  AppErrorOptions,
} from '../value-objects/validation';

export { AppError };

/**
 * ValidationError — input failed validation.
 */
export class ValidationError extends AppError {
  public readonly path?: string;
  public override readonly name = 'ValidationError';

  public constructor(
    message: string,
    options: AppErrorOptions & { readonly path?: string },
  ) {
    super(message, options);
    if (options.path !== undefined) {
      this.path = options.path;
    }
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * CompilationError — protocol/source failed to compile.
 */
export class CompilationError extends AppError {
  public readonly source?: string;
  public override readonly name = 'CompilationError';

  public constructor(
    message: string,
    options: AppErrorOptions & { readonly source?: string },
  ) {
    super(message, options);
    if (options.source !== undefined) {
      this.source = options.source;
    }
    Object.setPrototypeOf(this, CompilationError.prototype);
  }
}

/**
 * EngineError — generic engine failure.
 */
export class EngineError extends AppError {
  public override readonly name = 'EngineError';

  public constructor(message: string, options: AppErrorOptions) {
    super(message, options);
    Object.setPrototypeOf(this, EngineError.prototype);
  }
}

/**
 * ProtocolError — protocol-specific failure (invalid state, missing field).
 */
export class ProtocolError extends AppError {
  public override readonly name = 'ProtocolError';

  public constructor(message: string, options: AppErrorOptions) {
    super(message, options);
    Object.setPrototypeOf(this, ProtocolError.prototype);
  }
}

/**
 * TimerError — Timer Engine specific failure.
 */
export class TimerError extends AppError {
  public override readonly name = 'TimerError';

  public constructor(message: string, options: AppErrorOptions) {
    super(message, options);
    Object.setPrototypeOf(this, TimerError.prototype);
  }
}

/**
 * BreathError — Breath Engine specific failure.
 */
export class BreathError extends AppError {
  public override readonly name = 'BreathError';

  public constructor(message: string, options: AppErrorOptions) {
    super(message, options);
    Object.setPrototypeOf(this, BreathError.prototype);
  }
}