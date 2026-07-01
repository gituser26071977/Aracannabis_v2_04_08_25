/**
 * SessionRecorder — in-memory recorder for Session events.
 *
 * Responsibilities:
 *   - record every event the Session emits (subscribes to Session
 *     API indirectly: consumers call record(event) after they
 *     observe each event via session.events())
 *   - expose the captured event list (read-only)
 *   - export a SessionRecording (frozen, JSON-serializable)
 *   - import a SessionRecording into a new Recorder
 *
 * No persistence — Recorder is in-memory only. Storage will be
 * implemented in a future sprint.
 */

import type { ProtocolId, SessionId } from '@araflow/shared-contracts';

import type { ExecutionPlanId, SessionEvent } from '@core/execution-session';

import type { SessionRecording } from '../domain/SessionRecording';
import { RECORDING_VERSION } from '../domain/SessionRecording';
import { fromJson, toJson, type JsonSessionRecording } from '../util/recording-format';

export class SessionRecorder {
  private entries: readonly SessionEvent[] = Object.freeze([]);
  private readonly _sessionId: SessionId | null;
  private readonly _protocolId: ProtocolId | null;
  private readonly _executionPlanId: ExecutionPlanId | null;

  constructor(deps?: {
    readonly sessionId?: SessionId;
    readonly protocolId?: ProtocolId;
    readonly executionPlanId?: ExecutionPlanId;
  }) {
    this._sessionId = deps?.sessionId ?? null;
    this._protocolId = deps?.protocolId ?? null;
    this._executionPlanId = deps?.executionPlanId ?? null;
  }

  public record = (event: SessionEvent): void => {
    const next = [...this.entries, event];
    this.entries = Object.freeze(next);
  };

  public recordMany = (events: readonly SessionEvent[]): void => {
    if (events.length === 0) {
      return;
    }
    const next = [...this.entries, ...events];
    this.entries = Object.freeze(next);
  };

  public events = (): readonly SessionEvent[] => this.entries;

  public size = (): number => this.entries.length;

  public sessionId = (): SessionId | null => this._sessionId;
  public protocolId = (): ProtocolId | null => this._protocolId;
  public executionPlanId = (): ExecutionPlanId | null => this._executionPlanId;

  public clear = (): void => {
    this.entries = Object.freeze([]);
  };

  public export = (recordedAtMonotonicMs: number): SessionRecording => {
    if (this._sessionId === null || this._protocolId === null || this._executionPlanId === null) {
      throw new Error('Recorder missing identity; cannot export a SessionRecording');
    }
    return Object.freeze({
      version: RECORDING_VERSION,
      sessionId: this._sessionId,
      protocolId: this._protocolId,
      executionPlanId: this._executionPlanId,
      recordedAtMonotonicMs,
      eventCount: this.entries.length,
      events: this.entries,
    });
  };

  public exportJson = (recordedAtMonotonicMs: number): JsonSessionRecording =>
    toJson(this.export(recordedAtMonotonicMs));

  public static import = (recording: SessionRecording): SessionRecorder => {
    const recorder = new SessionRecorder({
      sessionId: recording.sessionId,
      protocolId: recording.protocolId,
      executionPlanId: recording.executionPlanId,
    });
    recorder.recordMany(recording.events);
    return recorder;
  };

  public static importJson = (raw: unknown): SessionRecorder => {
    return SessionRecorder.import(fromJson(raw));
  };
}
