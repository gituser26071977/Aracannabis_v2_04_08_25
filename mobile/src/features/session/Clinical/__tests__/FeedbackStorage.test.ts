/**
 * FeedbackStorage — unit tests.
 *
 * Validates the AsyncStorage wrapper: keys are derived from the
 * session start ISO, the index is updated, and listFeedback returns
 * a stable view.
 *
 * AsyncStorage is mocked via the official `async-storage-mock`
 * module (installed by the React Native preset) — we install it
 * directly in case the global mock has not been wired.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  buildFeedbackKey,
  clearAllFeedback,
  FEEDBACK_STORAGE_PREFIX,
  isFeedbackRecord,
  listFeedback,
  saveFeedback,
} from '../feedback/FeedbackStorage';
import { FEELING_AFTER_OPTIONS, isFeelingAfter } from '../feedback/FEELING_AFTER_OPTIONS';

// AsyncStorage is mocked by the React Native jest preset.
interface AsyncStorageMock extends jest.Mock {
  setItem: jest.Mock;
  getItem: jest.Mock;
  removeItem: jest.Mock;
  multiGet: jest.Mock;
  multiRemove: jest.Mock;
  clear: jest.Mock;
}

const asMock = AsyncStorage as unknown as AsyncStorageMock;

describe('FeedbackStorage — buildFeedbackKey', () => {
  it('prefixes the key with FEEDBACK_STORAGE_PREFIX', () => {
    expect(buildFeedbackKey('2026-07-01T000000000Z')).toBe(
      `${FEEDBACK_STORAGE_PREFIX}2026-07-01T000000000Z`,
    );
  });

  it('sanitizes non-alphanumeric characters (colons, slashes, spaces)', () => {
    expect(buildFeedbackKey('a/b c:d-e')).toBe(`${FEEDBACK_STORAGE_PREFIX}a_b_c_d-e`);
  });
});

describe('FeedbackStorage — saveFeedback / listFeedback', () => {
  beforeEach(async () => {
    await asMock.clear();
  });

  afterAll(async () => {
    await asMock.clear();
  });

  it('writes the entry to AsyncStorage and returns the resolved key', async () => {
    const entry = await saveFeedback({
      sessionStartIso: '2026-07-01T00:00:00.000Z',
      protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FA2',
      protocolTitle: 'Respiração Diafragmática',
      feeling: 'better',
      sessionDurationMs: 84000,
      completed: true,
      recordedAtIso: '2026-07-01T00:01:24.000Z',
    });
    expect(entry.storageKey).toBe(buildFeedbackKey('2026-07-01T00:00:00.000Z'));
    expect(entry.feeling).toBe('better');
    const raw = await asMock.getItem(entry.storageKey);
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw as string);
    expect(parsed.feeling).toBe('better');
  });

  it('appends (does not overwrite) multiple entries', async () => {
    await saveFeedback({
      sessionStartIso: '2026-07-01T00:00:00.000Z',
      protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FA2',
      protocolTitle: 'Diaphragmatic',
      feeling: 'better',
      sessionDurationMs: 84000,
      completed: true,
      recordedAtIso: '2026-07-01T00:01:00.000Z',
    });
    await saveFeedback({
      sessionStartIso: '2026-07-01T00:02:00.000Z',
      protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FBX',
      protocolTitle: 'Box',
      feeling: 'much-better',
      sessionDurationMs: 96000,
      completed: true,
      recordedAtIso: '2026-07-01T00:03:00.000Z',
    });
    const all = await listFeedback();
    expect(all.length).toBe(2);
    const feelings = all.map((e) => e.feeling).sort();
    expect(feelings).toEqual(['better', 'much-better']);
  });

  it('listFeedback returns empty array when nothing is stored', async () => {
    await asMock.clear();
    const all = await listFeedback();
    expect(all.length).toBe(0);
  });

  it('clearAllFeedback removes every entry and the index', async () => {
    await saveFeedback({
      sessionStartIso: '2026-07-01T00:00:00.000Z',
      protocolId: '01ARZ3NDEKTSV4RRFFQ69G5FA2',
      protocolTitle: 'Diaphragmatic',
      feeling: 'same',
      sessionDurationMs: 1000,
      completed: false,
      recordedAtIso: '2026-07-01T00:00:01.000Z',
    });
    expect((await listFeedback()).length).toBe(1);
    await clearAllFeedback();
    expect((await listFeedback()).length).toBe(0);
  });

  it('isFeedbackRecord accepts a valid record', () => {
    expect(
      isFeedbackRecord({
        protocolId: 'a',
        protocolTitle: 'b',
        feeling: 'better',
        sessionDurationMs: 1,
        completed: true,
        recordedAtIso: '2026-07-01T00:00:00.000Z',
      }),
    ).toBe(true);
  });

  it('isFeedbackRecord rejects an invalid feeling', () => {
    expect(
      isFeedbackRecord({
        protocolId: 'a',
        protocolTitle: 'b',
        feeling: 'delighted',
        sessionDurationMs: 1,
        completed: true,
        recordedAtIso: '2026-07-01T00:00:00.000Z',
      }),
    ).toBe(false);
  });
});

describe('FEELING_AFTER_OPTIONS', () => {
  it('has exactly 5 options in the canonical order', () => {
    expect(FEELING_AFTER_OPTIONS).toEqual(['much-worse', 'worse', 'same', 'better', 'much-better']);
  });

  it('isFeelingAfter accepts every member', () => {
    for (const f of FEELING_AFTER_OPTIONS) {
      expect(isFeelingAfter(f)).toBe(true);
    }
  });

  it('isFeelingAfter rejects unknown strings', () => {
    expect(isFeelingAfter('amazing')).toBe(false);
    expect(isFeelingAfter(null)).toBe(false);
    expect(isFeelingAfter(undefined)).toBe(false);
    expect(isFeelingAfter(42)).toBe(false);
  });
});
