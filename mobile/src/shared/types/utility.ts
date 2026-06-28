/**
 * Utility types — pure TS, no runtime code.
 */

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

export type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

export type NonEmptyArray<T> = readonly [T, ...T[]];

export type ValueOf<T> = T[keyof T];

export type AsyncOrSync<T> = T | Promise<T>;

export type Primitive = string | number | boolean | null | undefined | symbol | bigint;

export type Exact<T, Shape> = T extends Shape
  ? Shape extends T
    ? T
    : never
  : never;
