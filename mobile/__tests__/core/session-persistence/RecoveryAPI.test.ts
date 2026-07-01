/**
 * Tests for RecoveryAPI — canRecover / recover / discard.
 *
 * No auto-recovery: every test asserts explicit consumer behavior.
 */

import {
  createJsonSerializer,
  createMemoryStorageAdapter,
  createPersistenceService,
  createRecoveryAPI,
  type RecoveryAPI,
} from '@core/session-persistence';
import { sessionToPersistedSnapshot } from '@core/session-persistence';

import { buildFakeSession, SESSION_ID } from './fakes';

const buildRecovery = (): { recovery: RecoveryAPI; save: (snap: unknown) => Promise<void> } => {
  const adapter = createMemoryStorageAdapter();
  const persistence = createPersistenceService({
    serializer: createJsonSerializer(),
    storage: adapter,
  });
  const recovery = createRecoveryAPI({ persistence });
  return {
    recovery,
    save: async (snap): Promise<void> => {
      await adapter.write(SESSION_ID, JSON.stringify(snap));
    },
  };
};

describe('RecoveryAPI — canRecover', () => {
  it('returns canRecover=false when nothing is persisted', async () => {
    const { recovery } = buildRecovery();
    const probe = await recovery.canRecover(SESSION_ID);
    expect(probe.canRecover).toBe(false);
    expect(probe.reason).toBe('no-snapshot');
    expect(probe.snapshotVersion).toBeNull();
  });

  it('returns canRecover=true when a valid snapshot exists', async () => {
    const adapter = createMemoryStorageAdapter();
    const persistence = createPersistenceService({
      serializer: createJsonSerializer(),
      storage: adapter,
    });
    const recovery = createRecoveryAPI({ persistence });

    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await persistence.save({ sessionId: SESSION_ID, snapshot: snap });

    const probe = await recovery.canRecover(SESSION_ID);
    expect(probe.canRecover).toBe(true);
    expect(probe.reason).toBe('recoverable');
    expect(probe.snapshotVersion).toBe(1);
  });

  it('returns canRecover=false when payload is corrupted', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write(SESSION_ID, '{not json');
    const probe = await createRecoveryAPI({
      persistence: createPersistenceService({
        serializer: createJsonSerializer(),
        storage: adapter,
      }),
    }).canRecover(SESSION_ID);
    expect(probe.canRecover).toBe(false);
    expect(probe.reason).toBe('corrupted');
  });
});

describe('RecoveryAPI — recover', () => {
  it('returns ok=true with the snapshot when present', async () => {
    const adapter = createMemoryStorageAdapter();
    const persistence = createPersistenceService({
      serializer: createJsonSerializer(),
      storage: adapter,
    });
    const recovery = createRecoveryAPI({ persistence });

    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await persistence.save({ sessionId: SESSION_ID, snapshot: snap });

    const result = await recovery.recover(SESSION_ID);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.snapshot.metadata.sessionId).toBe(SESSION_ID);
    }
  });

  it('returns ok=false with reason=no-snapshot when missing', async () => {
    const { recovery } = buildRecovery();
    const result = await recovery.recover(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('no-snapshot');
    }
  });

  it('returns ok=false with reason=corrupted when payload invalid', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write(SESSION_ID, '{not json');
    const recovery = createRecoveryAPI({
      persistence: createPersistenceService({
        serializer: createJsonSerializer(),
        storage: adapter,
      }),
    });
    const result = await recovery.recover(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('corrupted');
    }
  });
});

describe('RecoveryAPI — discard', () => {
  it('removes the persisted snapshot', async () => {
    const adapter = createMemoryStorageAdapter();
    const persistence = createPersistenceService({
      serializer: createJsonSerializer(),
      storage: adapter,
    });
    const recovery = createRecoveryAPI({ persistence });

    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await persistence.save({ sessionId: SESSION_ID, snapshot: snap });
    expect(await persistence.exists(SESSION_ID)).toBe(true);

    await recovery.discard(SESSION_ID);
    expect(await persistence.exists(SESSION_ID)).toBe(false);
  });

  it('is a no-op when nothing is stored', async () => {
    const { recovery } = buildRecovery();
    await expect(recovery.discard(SESSION_ID)).resolves.toBeUndefined();
  });
});

describe('RecoveryAPI — sanity', () => {
  it('exposes recoveryId', () => {
    const { recovery } = buildRecovery();
    expect(recovery.recoveryId).toBe('recovery-api-v1');
  });
});
