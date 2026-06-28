/**
 * Either<L, R> — sum type with two branches (left = error/failure, right = success).
 *
 * Use Either when both branches can carry data, in contrast to:
 *   - Option<T>: just presence/absence
 *   - Result<T, E>: ok or error
 *
 * Convention: Left = "the alternative/negative", Right = "the primary/positive".
 * This convention mirrors Haskell/functional programming tradition.
 */

export type Either<L, R> =
  | { readonly left: L }
  | { readonly right: R };

export const Left = <L>(value: L): Either<L, never> => Object.freeze({ left: value });

export const Right = <R>(value: R): Either<never, R> => Object.freeze({ right: value });

export const isLeft = <L, R>(e: Either<L, R>): e is { left: L } =>
  'left' in e && !('right' in e);

export const isRight = <L, R>(e: Either<L, R>): e is { right: R } =>
  'right' in e && !('left' in e);

export const mapLeft = <L, L2, R>(e: Either<L, R>, fn: (left: L) => L2): Either<L2, R> =>
  isLeft(e) ? Left(fn(e.left)) : e;

export const mapRight = <L, R, R2>(e: Either<L, R>, fn: (right: R) => R2): Either<L, R2> =>
  isRight(e) ? Right(fn(e.right)) : e;

export const unwrapEither = <L, R>(e: Either<L, R>, defaultLeft: L): R =>
  isRight(e) ? e.right : defaultLeft;