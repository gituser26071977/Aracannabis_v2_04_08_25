/**
 * Type guards and assertion utilities.
 */

export const isString = (value: unknown): value is string => typeof value === 'string';
export const isNumber = (value: unknown): value is number =>
  typeof value === 'number' && !Number.isNaN(value);
export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean';
export const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
export const isFunction = (value: unknown): value is (...args: never[]) => unknown =>
  typeof value === 'function';
export const isDefined = <T>(value: T | null | undefined): value is T =>
  value !== null && value !== undefined;

export const assertNever = (value: never): never => {
  throw new Error(`Unexpected value: ${String(value)}`);
};

export const assertDefined = <T>(
  value: T | null | undefined,
  message = 'Value must be defined',
): T => {
  if (value === null || value === undefined) {
    throw new Error(message);
  }
  return value;
};
