/**
 * Tests for PersistenceService — save/load/delete/exists/list/clear,
 * error mapping, and migration integration.
 */

import {
  createJsonSerializer,
  createMemoryStorageAdapter,
  createMigrationRegistry,
  createPersistenceService,
  type SessionPersistence,
} from '@core/session-persistence';
import { sessionToPersistedSnapshot } from '@core/session-persistence';

import {
  buildFakeSession,
  EXECUTION_PLAN_ID,
  PROTOCOL_ID,
  SESSION_ID,
  startSession,
} from './fakes';

const buildService = (): {
  service: SessionPersistence;
  adapter: ReturnType<typeof createMemoryStorageAdapter>;
} => {
  const adapter = createMemoryStorageAdapter();
  const service = createPersistenceService({
    serializer: createJsonSerializer(),
    storage: adapter,
  });
  return { service, adapter };
};

describe('PersistenceService — save/load', () => {
  it('save + load round-trips a snapshot', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });

    const saveResult = await service.save({ sessionId: SESSION_ID, snapshot: snap });
    expect(saveResult.ok).toBe(true);
    if (!saveResult.ok) {
      return;
    }

    const loadResult = await service.load(SESSION_ID);
    expect(loadResult.ok).toBe(true);
    if (!loadResult.ok) {
      return;
    }
    expect(loadResult.snapshot).toEqual(snap);
    expect(loadResult.bytesRead).toBe(saveResult.bytesWritten);
  });

  it('save returns bytesWritten > 0', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    const result = await service.save({ sessionId: SESSION_ID, snapshot: snap });
    if (result.ok) {
      expect(result.bytesWritten).toBeGreaterThan(0);
    }
  });

  it('save with overwrite=false rejects duplicates', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    const second = await service.save({
      sessionId: SESSION_ID,
      snapshot: snap,
      overwrite: false,
    });
    expect(second.ok).toBe(false);
    if (!second.ok) {
      expect(second.reason).toBe('serialize-failed');
    }
  });

  it('save with overwrite=true replaces existing', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const a = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
      label: 'a',
    });
    const b = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 100,
      serializerVersion: 1,
      label: 'b',
    });
    await service.save({ sessionId: SESSION_ID, snapshot: a });
    const second = await service.save({ sessionId: SESSION_ID, snapshot: b });
    expect(second.ok).toBe(true);
    const loaded = await service.load(SESSION_ID);
    if (loaded.ok) {
      expect(loaded.snapshot.metadata.capturedAtMonotonicMs).toBe(100);
      expect(loaded.snapshot.metadata.label).toBe('b');
    }
  });

  it('load returns not-found for unknown session', async () => {
    const { service } = buildService();
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('not-found');
    }
  });
});

describe('PersistenceService — running snapshot', () => {
  it('preserves events and metrics through round-trip', async () => {
    const { service } = buildService();
    const session = buildFakeSession({ now: (): number => 100 });
    startSession(session, (): number => 100);
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 200,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    const loaded = await service.load(SESSION_ID);
    if (loaded.ok) {
      expect(loaded.snapshot.state).toBe('running');
      expect(loaded.snapshot.events.length).toBeGreaterThan(0);
      expect(loaded.snapshot.metrics.elapsedMs).toBe(snap.metrics.elapsedMs);
    }
  });
});

describe('PersistenceService — exists / list / delete / clear', () => {
  it('exists flips to true after save', async () => {
    const { service } = buildService();
    expect(await service.exists(SESSION_ID)).toBe(false);
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    expect(await service.exists(SESSION_ID)).toBe(true);
  });

  it('list returns all saved session ids', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    const other = '01ARZ3NDEKTSV4RRFFQ69G5F02' as typeof SESSION_ID;
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    await service.save({ sessionId: other, snapshot: snap });
    const ids = await service.list();
    expect(ids).toContain(SESSION_ID);
    expect(ids).toContain(other);
  });

  it('delete removes a record', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    await service.delete(SESSION_ID);
    expect(await service.exists(SESSION_ID)).toBe(false);
  });

  it('delete is a no-op for unknown session', async () => {
    const { service } = buildService();
    await expect(service.delete(SESSION_ID)).resolves.toBeUndefined();
  });

  it('clear wipes every record', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    await service.clear();
    expect((await service.list()).length).toBe(0);
  });
});

describe('PersistenceService — corrupted payloads', () => {
  it('load returns corrupted for invalid JSON', async () => {
    const { service, adapter } = buildService();
    await adapter.write(SESSION_ID, '{not json');
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('corrupted');
    }
  });

  it('load returns corrupted when schemaVersion envelope is missing', async () => {
    const { service, adapter } = buildService();
    await adapter.write(SESSION_ID, JSON.stringify({ snapshot: {} }));
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('corrupted');
    }
  });

  it('load returns corrupted when snapshot is missing', async () => {
    const { service, adapter } = buildService();
    await adapter.write(SESSION_ID, JSON.stringify({ schemaVersion: 1 }));
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('corrupted');
    }
  });
});

describe('PersistenceService — migrations', () => {
  it('uses a registered migration decoder for legacy versions', async () => {
    const adapter = createMemoryStorageAdapter();
    const serializer = createJsonSerializer();

    // Hand-craft a legacy payload with schemaVersion 0 — pretend it
    // had the same shape (no migration needed), but tagged as 0.
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 0,
    });
    const legacyEnvelope = JSON.stringify({ schemaVersion: 0, snapshot: snap });

    await adapter.write(SESSION_ID, legacyEnvelope);

    const migrations = createMigrationRegistry().register(0, {
      schemaVersion: 0,
      decode: (encoded: string) => {
        const parsed = JSON.parse(encoded) as { snapshot: typeof snap };
        return parsed.snapshot;
      },
    });

    const service = createPersistenceService({ serializer, storage: adapter, migrations });
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.snapshot.metadata.sessionId).toBe(SESSION_ID);
    }
  });

  it('returns incompatible when no migration exists', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write(SESSION_ID, JSON.stringify({ schemaVersion: 99, snapshot: {} }));
    const service = createPersistenceService({
      serializer: createJsonSerializer(),
      storage: adapter,
    });
    const result = await service.load(SESSION_ID);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe('incompatible');
    }
  });
});

describe('PersistenceService — sanity', () => {
  it('exposes persistenceId', () => {
    const { service } = buildService();
    expect(service.persistenceId).toBe('persistence-service-v1');
  });

  it('plan survives a round-trip', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    const loaded = await service.load(SESSION_ID);
    if (loaded.ok) {
      expect(loaded.snapshot.plan).toEqual(snap.plan);
      expect(loaded.snapshot.plan.executionId).toBe(snap.plan.executionId);
    }
  });

  it('executionPlanId + protocolId + sessionId survive a round-trip', async () => {
    const { service } = buildService();
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    await service.save({ sessionId: SESSION_ID, snapshot: snap });
    const loaded = await service.load(SESSION_ID);
    if (loaded.ok) {
      expect(loaded.snapshot.metadata.sessionId).toBe(SESSION_ID);
      expect(loaded.snapshot.metadata.protocolId).toBe(PROTOCOL_ID);
      expect(loaded.snapshot.metadata.executionPlanId).toBe(EXECUTION_PLAN_ID);
    }
  });
});
