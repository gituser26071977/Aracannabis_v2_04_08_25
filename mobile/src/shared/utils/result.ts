/**
 * Result utilities — wrap async operations in Result<T, E>.
 */

import { Result, Ok, Err } from '@contracts/common';

export const isOk = <T, E>(r: Result<T, E>): r is { ok: true; value: T } => r.ok;
export const isErr = <T, E>(r: Result<T, E>): r is { ok: false; error: E } => !r.ok;

export const tryAsync = async <T, E = Error>(fn: () => Promise<T>): Promise<Result<T, E>> => {
  try {
    const value = await fn();
    return Ok<T>(value);
  } catch (error: unknown) {
    return Err<E>(error as E);
  }
};

export const trySync = <T, E = Error>(fn: () => T): Result<T, E> => {
  try {
    return Ok<T>(fn());
  } catch (error: unknown) {
    return Err<E>(error as E);
  }
};

export const mapResult = <T, U, E>(r: Result<T, E>, fn: (value: T) => U): Result<U, E> => {
  if (r.ok) {
    return Ok<U>(fn(r.value));
  }
  return Err<U, E>(r.error);
};

export const flatMapResult = <T, U, E>(
  r: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> => {
  if (r.ok) {
    return fn(r.value);
  }
  return Err<U, E>(r.error);
};
