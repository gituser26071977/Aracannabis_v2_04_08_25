/**
 * Tests for MemoryStorageAdapter — pure in-memory storage.
 */

import { createMemoryStorageAdapter } from '@core/session-persistence';

describe('MemoryStorageAdapter — basic CRUD', () => {
  it('has adapterId "memory"', () => {
    const adapter = createMemoryStorageAdapter();
    expect(adapter.adapterId).toBe('memory');
  });

  it('returns null payload when reading a missing key', async () => {
    const adapter = createMemoryStorageAdapter();
    const result = await adapter.read('nope');
    expect(result.payload).toBeNull();
    expect(typeof result.updatedAtMonotonicMs).toBe('number');
  });

  it('write + read round-trips a payload', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('s1', 'payload-1');
    const result = await adapter.read('s1');
    expect(result.payload).toBe('payload-1');
  });

  it('exists returns false before write', async () => {
    const adapter = createMemoryStorageAdapter();
    expect(await adapter.exists('s1')).toBe(false);
    await adapter.write('s1', 'x');
    expect(await adapter.exists('s1')).toBe(true);
  });

  it('delete removes a record (no-op when missing)', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('s1', 'x');
    await adapter.delete('s1');
    expect(await adapter.exists('s1')).toBe(false);
    await expect(adapter.delete('nope')).resolves.toBeUndefined();
  });

  it('list returns every stored key', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('a', '1');
    await adapter.write('b', '2');
    await adapter.write('c', '3');
    expect([...(await adapter.list())].sort()).toEqual(['a', 'b', 'c']);
  });

  it('clear removes every record', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('a', '1');
    await adapter.write('b', '2');
    await adapter.clear();
    expect(await adapter.list()).toEqual([]);
  });
});

describe('MemoryStorageAdapter — write options', () => {
  it('overwrite=true (default) replaces existing payload', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('s1', 'first');
    await adapter.write('s1', 'second');
    expect((await adapter.read('s1')).payload).toBe('second');
  });

  it('overwrite=false throws when key exists', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('s1', 'first');
    await expect(adapter.write('s1', 'second', { overwrite: false })).rejects.toThrow(
      /already exists/,
    );
  });

  it('overwrite=false succeeds when key missing', async () => {
    const adapter = createMemoryStorageAdapter();
    await adapter.write('s1', 'first', { overwrite: false });
    expect((await adapter.read('s1')).payload).toBe('first');
  });
});

describe('MemoryStorageAdapter — monotonic timestamp', () => {
  it('updatedAtMonotonicMs increases with each write', async () => {
    let now = 0;
    const adapter = createMemoryStorageAdapter({ now: (): number => now });
    await adapter.write('s1', 'a');
    const first = (await adapter.read('s1')).updatedAtMonotonicMs;
    now = 100;
    await adapter.write('s1', 'b');
    const second = (await adapter.read('s1')).updatedAtMonotonicMs;
    expect(second).toBeGreaterThan(first);
  });
});
