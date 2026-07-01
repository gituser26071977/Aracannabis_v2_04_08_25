/**
 * Tests for the type guards.
 */

import {
  isRecoveryProbe,
  isSnapshotLifecycleStage,
  isSnapshotMetadata,
  isStorageRecord,
} from '@core/session-persistence';

describe('isSnapshotLifecycleStage', () => {
  it('accepts valid stages', () => {
    expect(isSnapshotLifecycleStage('in-flight')).toBe(true);
    expect(isSnapshotLifecycleStage('terminal')).toBe(true);
  });

  it('rejects invalid stages', () => {
    expect(isSnapshotLifecycleStage('paused')).toBe(false);
    expect(isSnapshotLifecycleStage('')).toBe(false);
    expect(isSnapshotLifecycleStage(null)).toBe(false);
  });
});

describe('isSnapshotMetadata', () => {
  const base = {
    snapshotId: 'snap_1',
    sessionId: '01ARZ3NDEKTSV4RRFFQ69G5F01',
    protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
    executionPlanId: '01HXYZ00000000000000000000',
    stage: 'in-flight' as const,
    capturedAtMonotonicMs: 0,
    updatedAtMonotonicMs: 0,
    serializerVersion: 1,
  };

  it('accepts valid metadata', () => {
    expect(isSnapshotMetadata(base)).toBe(true);
  });

  it('rejects non-objects', () => {
    expect(isSnapshotMetadata(null)).toBe(false);
    expect(isSnapshotMetadata(123)).toBe(false);
  });

  it('rejects wrong stage', () => {
    expect(isSnapshotMetadata({ ...base, stage: 'broken' })).toBe(false);
  });

  it('rejects missing fields', () => {
    const { snapshotId: _drop, ...rest } = base;
    if (_drop === undefined) {
      throw new Error('expected snapshotId to be defined');
    }
    expect(isSnapshotMetadata(rest)).toBe(false);
  });
});

describe('isStorageRecord', () => {
  it('accepts a valid record', () => {
    expect(
      isStorageRecord({
        format: 'araflow.session-snapshot',
        schemaVersion: 1,
        sessionId: 's1',
        payload: '{}',
      }),
    ).toBe(true);
  });

  it('rejects wrong format', () => {
    expect(
      isStorageRecord({
        format: 'other',
        schemaVersion: 1,
        sessionId: 's1',
        payload: '{}',
      }),
    ).toBe(false);
  });

  it('rejects non-string payload', () => {
    expect(
      isStorageRecord({
        format: 'araflow.session-snapshot',
        schemaVersion: 1,
        sessionId: 's1',
        payload: 123,
      }),
    ).toBe(false);
  });

  it('rejects non-object', () => {
    expect(isStorageRecord(null)).toBe(false);
  });
});

describe('isRecoveryProbe', () => {
  it('accepts a valid probe', () => {
    expect(
      isRecoveryProbe({
        sessionId: 's1',
        canRecover: true,
        reason: 'recoverable',
        snapshotVersion: 1,
      }),
    ).toBe(true);
  });

  it('accepts null snapshotVersion', () => {
    expect(
      isRecoveryProbe({
        sessionId: 's1',
        canRecover: false,
        reason: 'no-snapshot',
        snapshotVersion: null,
      }),
    ).toBe(true);
  });

  it('rejects malformed probe', () => {
    expect(isRecoveryProbe(null)).toBe(false);
    expect(isRecoveryProbe({})).toBe(false);
  });
});
