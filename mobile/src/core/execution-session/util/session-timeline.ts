/**
 * session-timeline — pure projection from event log to SessionTimeline.
 *
 * Builds an ordered, UI-independent list of session beats suitable for
 * rendering. Each entry's `durationMs` is the time spent in that beat.
 *
 * The timeline aggregates consecutive events of the same kind so the
 * UI can render "00:00 → 00:15 Inhale" rather than one entry per tick.
 */

import type { BreathPhase } from '@araflow/shared-contracts';

import type { SessionEvent } from '../domain/SessionEvent';
import type {
  SessionTimeline,
  SessionTimelineEntry,
  SessionTimelineKind,
} from '../domain/SessionTimeline';

const phaseToKind = (phase: BreathPhase): SessionTimelineKind => {
  switch (phase) {
    case 'inhaling':
      return 'inhale';
    case 'exhaling':
      return 'exhale';
    case 'holdAfterInhale':
    case 'holdAfterExhale':
      return 'hold';
  }
};

interface LifecycleKindResult {
  kind: SessionTimelineKind;
  phase?: BreathPhase;
  cycleIndex?: number;
  phaseIndex?: number;
}

const lifecycleKind = (ev: SessionEvent): LifecycleKindResult | null => {
  switch (ev.type) {
    case 'session-preparing':
      return { kind: 'prepare' };
    case 'session-started':
      return null;
    case 'session-paused':
      return { kind: 'pause' };
    case 'session-resumed':
      return { kind: 'resume' };
    case 'session-cancelled':
      return { kind: 'cancel' };
    case 'session-completed':
      return { kind: 'complete' };
    case 'session-failed':
      return { kind: 'fail' };
    case 'session-interrupted':
      return { kind: 'interrupt' };
    case 'phase-changed':
      return {
        kind: phaseToKind(ev.phase),
        phase: ev.phase,
        cycleIndex: ev.cycleIndex,
        phaseIndex: ev.phaseIndex,
      };
    case 'cycle-completed':
      return { kind: 'cycle', cycleIndex: ev.cycleIndex };
    default:
      return null;
  }
};

const isMergeableKind = (kind: SessionTimelineKind): boolean =>
  kind === 'inhale' || kind === 'exhale' || kind === 'hold';

export const buildTimeline = (events: readonly SessionEvent[]): SessionTimeline => {
  const out: SessionTimelineEntry[] = [];
  let lastEntry: SessionTimelineEntry | null = null;

  for (const ev of events) {
    const mapped = lifecycleKind(ev);
    if (mapped === null) {
      continue;
    }

    // Merge consecutive same-kind entries (e.g. two hold phases → one hold).
    const canMerge =
      lastEntry !== null && lastEntry.kind === mapped.kind && isMergeableKind(mapped.kind);

    if (canMerge && lastEntry !== null) {
      const duration = Math.max(0, ev.monotonicMs - lastEntry.monotonicMs);
      const merged: SessionTimelineEntry = Object.freeze({
        ...lastEntry,
        durationMs: lastEntry.durationMs + duration,
      });
      out[out.length - 1] = merged;
      lastEntry = merged;
      continue;
    }

    const entry: SessionTimelineEntry = Object.freeze({
      monotonicMs: ev.monotonicMs,
      durationMs: 0,
      kind: mapped.kind,
      ...(mapped.phase !== undefined ? { phase: mapped.phase } : {}),
      ...(mapped.cycleIndex !== undefined ? { cycleIndex: mapped.cycleIndex } : {}),
      ...(mapped.phaseIndex !== undefined ? { phaseIndex: mapped.phaseIndex } : {}),
    });
    out.push(entry);
    lastEntry = entry;
  }

  // Close open duration: last entry's duration spans until session end
  // (if terminated) or is left at 0 (still in flight).
  const last = events[events.length - 1];
  if (last === undefined || out.length === 0) {
    return Object.freeze(out);
  }

  const finalEntry = out[out.length - 1];
  const terminal =
    last.type === 'session-completed' ||
    last.type === 'session-cancelled' ||
    last.type === 'session-failed' ||
    last.type === 'session-interrupted';

  if (!terminal || finalEntry === undefined) {
    return Object.freeze(out);
  }

  if (
    finalEntry.kind === 'complete' ||
    finalEntry.kind === 'cancel' ||
    finalEntry.kind === 'fail' ||
    finalEntry.kind === 'interrupt'
  ) {
    return Object.freeze(out);
  }

  // The last timeline entry is non-terminal — close its duration
  // up to the terminal event's timestamp.
  out[out.length - 1] = Object.freeze({
    ...finalEntry,
    durationMs: Math.max(0, last.monotonicMs - finalEntry.monotonicMs),
  });
  return Object.freeze(out);
};
