/**
 * TimeUnit — canonical time unit enum + conversion helpers.
 *
 * All durations in the AraFlow system are stored in MILLISECONDS (the
 * canonical unit). This module provides conversions from human-friendly
 * units (seconds, minutes, hours) to milliseconds and vice versa.
 */

export const TIME_UNITS = [
  'millisecond',
  'second',
  'minute',
  'hour',
  'day',
] as const;

export type TimeUnit = (typeof TIME_UNITS)[number];

const UNIT_TO_MS: Readonly<Record<TimeUnit, number>> = Object.freeze({
  millisecond: 1,
  second: 1_000,
  minute: 60_000,
  hour: 3_600_000,
  day: 86_400_000,
});

export const toMilliseconds = (value: number, unit: TimeUnit): number =>
  value * (UNIT_TO_MS[unit]);

export const fromMilliseconds = (value: number, unit: TimeUnit): number =>
  value / (UNIT_TO_MS[unit]);

export const isTimeUnit = (v: unknown): v is TimeUnit =>
  typeof v === 'string' && (TIME_UNITS as readonly string[]).includes(v);