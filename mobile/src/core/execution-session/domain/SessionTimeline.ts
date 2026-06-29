/**
 * SessionTimeline — ordered list of human-meaningful session beats.
 *
 * Each entry describes a single phase/transition with its start time
 * and duration. The timeline is UI-independent (no colors, no icons,
 * no formatting strings) — UI layers render it however they want.
 */

import type { BreathPhase } from '@araflow/shared-contracts';

export type SessionTimelineKind =
  | 'prepare'
  | 'inhale'
  | 'exhale'
  | 'hold'
  | 'cycle'
  | 'pause'
  | 'resume'
  | 'complete'
  | 'cancel'
  | 'fail'
  | 'interrupt';

export interface SessionTimelineEntry {
  readonly monotonicMs: number;
  readonly durationMs: number;
  readonly kind: SessionTimelineKind;
  readonly phase?: BreathPhase;
  readonly cycleIndex?: number;
  readonly phaseIndex?: number;
}

export type SessionTimeline = readonly SessionTimelineEntry[];
