/**
 * Tests for MigrationRegistry — register / find / versions.
 */

import { createJsonSerializer, createMigrationRegistry } from '@core/session-persistence';

describe('MigrationRegistry', () => {
  it('finds a registered decoder', () => {
    const decoder = {
      schemaVersion: 0,
      decode: (s: string) => JSON.parse(s) as never,
    };
    const registry = createMigrationRegistry().register(0, decoder);
    expect(registry.find(0)).toBe(decoder);
  });

  it('returns undefined when not found', () => {
    const registry = createMigrationRegistry();
    expect(registry.find(1)).toBeUndefined();
  });

  it('versions() returns registered versions sorted ascending', () => {
    const registry = createMigrationRegistry()
      .register(5, createJsonSerializer())
      .register(1, createJsonSerializer())
      .register(3, createJsonSerializer());
    expect(registry.versions()).toEqual([1, 3, 5]);
  });

  it('overwrites a decoder for an already-registered version', () => {
    const a = { schemaVersion: 1, decode: (s: string) => JSON.parse(s) as never };
    const b = { schemaVersion: 1, decode: (s: string) => JSON.parse(s) as never };
    const registry = createMigrationRegistry().register(1, a).register(1, b);
    expect(registry.find(1)).toBe(b);
  });

  it('register returns the registry (chainable)', () => {
    const registry = createMigrationRegistry();
    const result = registry.register(1, createJsonSerializer());
    expect(result).toBe(registry);
  });

  it('starts empty when no initial map provided', () => {
    const registry = createMigrationRegistry();
    expect(registry.versions()).toEqual([]);
  });

  it('accepts an initial map', () => {
    const initial = new Map([[2, createJsonSerializer()]]);
    const registry = createMigrationRegistry(initial);
    expect(registry.versions()).toEqual([2]);
  });
});
