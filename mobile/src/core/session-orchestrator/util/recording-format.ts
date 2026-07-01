/**
 * recording-format — pure utilities for converting between a
 * SessionRecording and its JSON-serializable form.
 *
 * No persistence: this only encodes/decodes the recording to a
 * portable object. Future persistence layers can store the JSON
 * form directly.
 */

import type { SessionEvent } from '@core/execution-session';

import type { SessionRecording } from '../domain/SessionRecording';
import { isSessionRecording, RECORDING_VERSION } from '../domain/SessionRecording';

export interface JsonSessionRecording {
  readonly version: typeof RECORDING_VERSION;
  readonly sessionId: string;
  readonly protocolId: string;
  readonly executionPlanId: string;
  readonly recordedAtMonotonicMs: number;
  readonly eventCount: number;
  readonly events: readonly SessionEvent[];
}

export const toJson = (recording: SessionRecording): JsonSessionRecording =>
  Object.freeze({
    version: RECORDING_VERSION,
    sessionId: recording.sessionId,
    protocolId: recording.protocolId,
    executionPlanId: recording.executionPlanId,
    recordedAtMonotonicMs: recording.recordedAtMonotonicMs,
    eventCount: recording.eventCount,
    events: recording.events,
  });

export const fromJson = (raw: unknown): SessionRecording => {
  if (!isSessionRecording(raw)) {
    throw new Error('Invalid SessionRecording: shape mismatch');
  }
  return Object.freeze({
    version: 1,
    sessionId: raw.sessionId,
    protocolId: raw.protocolId,
    executionPlanId: raw.executionPlanId,
    recordedAtMonotonicMs: raw.recordedAtMonotonicMs,
    eventCount: raw.eventCount,
    events: Object.freeze(raw.events.slice()),
  });
};
