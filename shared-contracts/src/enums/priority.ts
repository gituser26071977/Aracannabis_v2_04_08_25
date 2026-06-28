/**
 * Priority and Severity enums — for error handling and event prioritization.
 *
 * Priority: relative importance of an event or task.
 * Severity: severity of an error or warning.
 */

// =============================================================================
// Priority
// =============================================================================

/**
 * Priority levels, ordered from lowest (0) to highest (5).
 */
export const PRIORITIES = [
  'lowest',
  'low',
  'normal',
  'high',
  'highest',
  'critical',
] as const;

export type Priority = (typeof PRIORITIES)[number];

export const PRIORITY_RANK: Readonly<Record<Priority, number>> = Object.freeze({
  lowest: 0,
  low: 1,
  normal: 2,
  high: 3,
  highest: 4,
  critical: 5,
});

export const isPriority = (v: unknown): v is Priority =>
  typeof v === 'string' && (PRIORITIES as readonly string[]).includes(v);

// =============================================================================
// Severity
// =============================================================================

export const SEVERITIES = ['info', 'warn', 'error', 'fatal'] as const;

export type Severity = (typeof SEVERITIES)[number];

export const SEVERITY_RANK: Readonly<Record<Severity, number>> = Object.freeze({
  info: 0,
  warn: 1,
  error: 2,
  fatal: 3,
});

export const isSeverity = (v: unknown): v is Severity =>
  typeof v === 'string' && (SEVERITIES as readonly string[]).includes(v);