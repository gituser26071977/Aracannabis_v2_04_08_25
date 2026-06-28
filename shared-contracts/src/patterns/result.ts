/**
 * Result<T, E> — Rust-style success/error container.
 *
 * Use Result instead of throwing for expected error paths (validation,
 * user input, recoverable failures). Reserve throw for programmer errors
 * (invariant violations, impossible states).
 *
 * Pattern:
 *   const r = doSomething();
 *   if (r.ok) {
 *     useValue(r.value);
 *   } else {
 *     handleError(r.error);
 *   }
 */

import { AppError } from '../value-objects/validation';

export type Result<T, E = AppError> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const Ok = <T>(value: T): Result<T, never> => Object.freeze({ ok: true, value });

export const Err = <E>(error: E): Result<never, E> => Object.freeze({ ok: false, error });

export const isOk = <T, E>(r: Result<T, E>): r is { ok: true; value: T } => r.ok;

export const isErr = <T, E>(r: Result<T, E>): r is { ok: false; error: E } => !r.ok;

/**
 * Maps the success value of a Result, leaving the error untouched.
 */
export const mapResult = <T, U, E>(
  r: Result<T, E>,
  fn: (value: T) => U,
): Result<U, E> => (r.ok ? Ok(fn(r.value)) : r);

/**
 * Maps the error of a Result, leaving the success untouched.
 */
export const mapError = <T, E, F>(
  r: Result<T, E>,
  fn: (error: E) => F,
): Result<T, F> => (r.ok ? r : Err(fn(r.error)));

/**
 * Chains Result-returning operations.
 */
export const flatMapResult = <T, U, E>(
  r: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> => (r.ok ? fn(r.value) : r);

/**
 * Unwraps the success value or throws the error.
 * Use sparingly; prefer pattern matching via `isOk`/`isErr`.
 */
export const unwrap = <T, E>(r: Result<T, E>): T => {
  if (r.ok) return r.value;
  throw r.error instanceof Error ? r.error : new Error(String(r.error));
};

/**
 * Unwraps the success value or returns the provided fallback.
 */
export const unwrapOr = <T, E>(r: Result<T, E>, fallback: T): T =>
  r.ok ? r.value : fallback;

/**
 * Combines a list of Results into a single Result containing all
 * values (if all ok) or the first error (if any failed).
 */
export const allResults = <T, E>(results: readonly Result<T, E>[]): Result<readonly T[], E> => {
  const values: T[] = [];
  for (const r of results) {
    if (!r.ok) return r;
    values.push(r.value);
  }
  return Ok(values);
};