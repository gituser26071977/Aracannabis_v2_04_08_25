/**
 * Option<T> — Rust-style optional value.
 *
 * Use Option for values that may or may not be present, where absence
 * is a normal state (not an error). For errors, use Result instead.
 *
 * Pattern:
 *   const maybe = findUser(id);
 *   if (maybe.some) {
 *     useUser(maybe.value);
 *   } else {
 *     // handle absence
 *   }
 */

export type Option<T> =
  | { readonly some: true; readonly value: T }
  | { readonly some: false };

export const Some = <T>(value: T): Option<T> => Object.freeze({ some: true, value });

export const None = <T>(): Option<T> => Object.freeze({ some: false });

export const isSome = <T>(o: Option<T>): o is { some: true; value: T } => o.some;

export const isNone = <T>(o: Option<T>): o is { some: false } => !o.some;

/**
 * Maps the value inside Some, leaving None untouched.
 */
export const mapOption = <T, U>(o: Option<T>, fn: (value: T) => U): Option<U> =>
  o.some ? Some(fn(o.value)) : None<U>();

/**
 * Chains Option-returning operations.
 */
export const flatMapOption = <T, U>(o: Option<T>, fn: (value: T) => Option<U>): Option<U> =>
  o.some ? fn(o.value) : None<U>();

/**
 * Returns the value if Some, otherwise the fallback.
 */
export const unwrapOptionOr = <T>(o: Option<T>, fallback: T): T =>
  o.some ? o.value : fallback;

/**
 * Combines two Options into a tuple, or None if either is None.
 */
export const zip2 = <A, B>(a: Option<A>, b: Option<B>): Option<readonly [A, B]> =>
  a.some && b.some ? Some([a.value, b.value] as const) : None();

/**
 * Returns the first Some value from a list, or None if all are None.
 */
export const firstSome = <T>(options: readonly Option<T>[]): Option<T> => {
  for (const o of options) {
    if (o.some) return o;
  }
  return None<T>();
};