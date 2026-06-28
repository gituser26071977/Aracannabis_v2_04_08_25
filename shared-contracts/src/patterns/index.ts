/**
 * Patterns — barrel.
 */

export {
  Ok,
  Err,
  isOk,
  isErr,
  mapResult,
  mapError,
  flatMapResult,
  unwrap,
  unwrapOr,
  allResults,
} from './result';

export type { Result } from './result';

export {
  Some,
  None,
  isSome,
  isNone,
  mapOption,
  flatMapOption,
  unwrapOptionOr,
  zip2,
  firstSome,
} from './option';

export type { Option } from './option';

export {
  Left,
  Right,
  isLeft,
  isRight,
  mapLeft,
  mapRight,
  unwrapEither,
} from './either';

export type { Either } from './either';

export {
  Failure,
  isFailure,
  groupFailuresBySeverity,
  hasBlockingFailures,
} from './failure';

export type { Failure as FailureType } from './failure';