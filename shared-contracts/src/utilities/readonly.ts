/**
 * DeepReadonly<T> — recursively makes all properties readonly.
 *
 * Use for snapshot types and immutable data structures. Note that
 * this is a TYPE-LEVEL constraint only; runtime mutation is not
 * prevented. Combine with Object.freeze for runtime immutability.
 */

export type DeepReadonly<T> =
  T extends (infer U)[]
    ? ReadonlyArray<DeepReadonly<U>>
    : T extends ReadonlyArray<infer U>
      ? ReadonlyArray<DeepReadonly<U>>
      : T extends object
        ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
        : T;

/**
 * Immutable<T> — alias for DeepReadonly<T>.
 *
 * Use this for data that is contractually immutable (snapshots,
 * frozen configs, audit logs).
 */
export type Immutable<T> = DeepReadonly<T>;