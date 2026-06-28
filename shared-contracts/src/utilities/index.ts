/**
 * Utilities — barrel.
 */

export type { DeepReadonly, Immutable } from './readonly';

export {
  generateUuidV4,
  validateUuidV4,
  generateUlidLike,
} from './uuid';

export {
  TIME_UNITS,
  toMilliseconds,
  fromMilliseconds,
  isTimeUnit,
} from './time-unit';

export type { TimeUnit } from './time-unit';