/**
 * replay-reducer — pure reducer that takes a SessionRecording and a
 * freshly-constructed ExecutionSession, then walks the recorded events
 * and drives the Session through the same API calls that originally
 * produced them.
 *
 * The reducer is a one-shot pure function: given the same recording
 * and the same starting Session (constructed from the recording's
 * identity), the resulting Session state is deterministic.
 *
 * Implementation:
 *   - The first event in a recording is always 'session-created'.
 *     The reducer verifies its identity matches the Session.
 *   - Every other event is replayed by mapping back to the Session
 *     API call that produced it.
 *   - The reducer returns a Result<void, EngineError>. Errors are
 *     produced by the Session itself (e.g. impossible transition).
 */

import { EngineError, Err, Ok, type Result, type SessionId } from '@araflow/shared-contracts';

import type { ExecutionSession, SessionEvent } from '@core/execution-session';

import type { SessionRecording } from '../domain/SessionRecording';

const missingEventError = (): EngineError =>
  new EngineError('Recording does not begin with session-created', {
    code: 'orchestrator_replay_missing_anchor',
    severity: 'error',
  });

const identityMismatchError = (expected: SessionId, actual: SessionId | undefined): EngineError =>
  new EngineError('Recording identity does not match Session identity', {
    code: 'REDACTED',
    severity: 'error',
    context: { expected, actual },
  });

const unexpectedEventError = (event: SessionEvent): EngineError =>
  new EngineError('Cannot replay non-lifecycle observation event without anchor', {
    code: 'REDACTED',
    severity: 'error',
    context: { type: event.type },
  });

export const replayInto = (input: {
  readonly session: ExecutionSession;
  readonly recording: SessionRecording;
}): Result<void, EngineError> => {
  const events = input.recording.events;
  if (events.length === 0) {
    return Err(missingEventError());
  }
  const anchor = events[0];
  if (anchor === undefined || anchor.type !== 'session-created') {
    return Err(missingEventError());
  }

  // Verify identity.
  const sessionIdentity = input.session.sessionId();
  if (anchor.sessionId !== sessionIdentity) {
    return Err(identityMismatchError(sessionIdentity, anchor.sessionId));
  }

  // Walk events; first is the anchor (already emitted by construction).
  for (let i = 1; i < events.length; i += 1) {
    const event = events[i];
    if (event === undefined) {
      continue;
    }
    const r = replayOne(input.session, event);
    if (!r.ok) {
      return r;
    }
  }
  return Ok(undefined);
};

const replayOne = (session: ExecutionSession, event: SessionEvent): Result<void, EngineError> => {
  switch (event.type) {
    case 'session-created':
      // Already handled at construction. Skip.
      return Ok(undefined);
    case 'session-preparing':
    case 'session-started':
      return session.start();
    case 'session-paused':
      return session.pause();
    case 'session-resumed':
      return session.resume();
    case 'session-cancelled':
      return session.cancel(event.reason);
    case 'session-completed':
      return session.complete();
    case 'session-failed':
      return session.fail(event.code, event.message);
    case 'session-interrupted':
      return session.interrupt(event.reason);
    case 'phase-changed':
      return session.recordPhaseChange({
        phase: event.phase,
        cycleIndex: event.cycleIndex,
        phaseIndex: event.phaseIndex,
        phaseElapsedMs: event.phaseElapsedMs,
        phaseDurationMs: event.phaseDurationMs,
        monotonicMs: event.monotonicMs,
      });
    case 'cycle-completed':
      return session.recordCycleCompleted({
        cycleIndex: event.cycleIndex,
        cycleElapsedMs: event.cycleElapsedMs,
        totalCycles: event.totalCycles,
        monotonicMs: event.monotonicMs,
      });
    case 'metric-updated':
    case 'snapshot-created':
      // Derived events are produced by the Session itself; skip.
      return Ok(undefined);
    default: {
      const unknown: never = event;
      return Err(unexpectedEventError(unknown as SessionEvent));
    }
  }
};
