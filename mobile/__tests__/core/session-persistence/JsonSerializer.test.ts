/**
 * Tests for JsonSerializer — round-trip, version envelope, errors.
 */

import { createJsonSerializer, sessionToPersistedSnapshot } from '@core/session-persistence';

import { buildFakeSession, startSession } from './fakes';

describe('JsonSerializer — encode/decode', () => {
  const serializer = createJsonSerializer();

  it('has the expected id and schemaVersion', () => {
    expect(serializer.serializerId).toBe('json-v1');
    expect(serializer.schemaVersion).toBe(1);
  });

  it('round-trips an idle snapshot', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    const encoded = serializer.encode(snap);
    const decoded = serializer.decode(encoded);
    expect(decoded).toEqual(snap);
  });

  it('round-trips a running snapshot with events', () => {
    const session = buildFakeSession({ now: (): number => 100 });
    startSession(session, (): number => 100);
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 200,
      serializerVersion: 1,
    });
    const encoded = serializer.encode(snap);
    const decoded = serializer.decode(encoded);
    expect(decoded.state).toBe('running');
    expect(decoded.events.length).toBeGreaterThan(0);
    expect(decoded.metrics.elapsedMs).toBe(snap.metrics.elapsedMs);
  });

  it('produces deterministic output for the same snapshot', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    expect(serializer.encode(snap)).toBe(serializer.encode(snap));
  });

  it('includes schemaVersion envelope at top level', () => {
    const session = buildFakeSession();
    const snap = sessionToPersistedSnapshot({
      session,
      capturedAtMonotonicMs: 0,
      serializerVersion: 1,
    });
    const encoded = serializer.encode(snap);
    expect(encoded.includes('"schemaVersion":1')).toBe(true);
  });
});

describe('JsonSerializer — decode errors', () => {
  const serializer = createJsonSerializer();

  it('rejects non-object payload', () => {
    expect(() => serializer.decode('null')).toThrow(/not an object/);
    expect(() => serializer.decode('123')).toThrow(/not an object/);
    expect(() => serializer.decode('"x"')).toThrow(/not an object/);
  });

  it('rejects missing schemaVersion', () => {
    expect(() => serializer.decode('{"snapshot":{}}')).toThrow(/schemaVersion/);
  });

  it('rejects unsupported schemaVersion', () => {
    expect(() => serializer.decode('{"schemaVersion":99,"snapshot":{}}')).toThrow(/not supported/);
  });

  it('rejects missing snapshot', () => {
    expect(() => serializer.decode('{"schemaVersion":1}')).toThrow(/missing snapshot/);
  });

  it('rejects malformed JSON', () => {
    expect(() => serializer.decode('{not json')).toThrow();
  });
});
