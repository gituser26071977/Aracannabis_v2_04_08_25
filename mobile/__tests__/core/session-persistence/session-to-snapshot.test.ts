/**
 * Tests for the session → persisted snapshot projection.
 */

import {
  sessionToPersistedSnapshot,
  type PersistedSessionSnapshot,
} from '@core/session-persistence';

import { buildFakeSession, startSession } from './fakes';

describe('sessionToPersistedSnapshot', () => {
  it('captures identity from the session', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    expect(snap.metadata.sessionId).toBe(session.sessionId());
    expect(snap.metadata.protocolId).toBe(session.protocolId());
    expect(snap.metadata.executionPlanId).toBe(session.executionPlanId());
  });

  it('captures the initial idle state', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    expect(snap.state).toBe('idle');
    expect(snap.metadata.stage).toBe('in-flight');
  });

  it('captures a running state as in-flight', () => {
    const session = buildFakeSession({ now: (): number => 100 });
    startSession(session, (): number => 100);
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 200,
      serializerVersion: 1,
    });
    expect(snap.state).toBe('running');
    expect(snap.metadata.stage).toBe('in-flight');
  });

  it('uses the provided snapshotId when supplied', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
      snapshotId: 'custom-id',
    });
    expect(snap.metadata.snapshotId).toBe('custom-id');
  });

  it('produces a deterministic snapshotId when none is supplied', () => {
    const session = buildFakeSession();
    const a = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 42,
      serializerVersion: 1,
    });
    const b = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 42,
      serializerVersion: 1,
    });
    expect(a.metadata.snapshotId).toBe(b.metadata.snapshotId);
  });

  it('forwards label to metadata', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
      label: 'morning session',
    });
    expect(snap.metadata.label).toBe('morning session');
  });

  it('captures events emitted before save', () => {
    const session = buildFakeSession({ now: (): number => 100 });
    startSession(session, (): number => 100);
    const snap: PersistedSessionSnapshot = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 200,
      serializerVersion: 1,
    });
    expect(snap.events.length).toBeGreaterThan(0);
    expect(snap.events[0]?.type).toBe('session-created');
  });

  it('captures plan + metrics + timeline', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    expect(snap.plan).toBeDefined();
    expect(snap.metrics).toBeDefined();
    expect(snap.timeline).toBeDefined();
  });
});
