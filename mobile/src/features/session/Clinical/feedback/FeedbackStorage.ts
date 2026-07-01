/**
 * Clinical MVP — FeedbackStorage.
 *
 * Persists post-session feedback to AsyncStorage (local-only). Each
 * feedback entry is stored under a stable key derived from the
 * session start ISO timestamp; `listFeedback` reads every key
 * belonging to AraFlow.
 *
 * The store is intentionally append-only and does not sync. It
 * lives in `features/` (not Core) per the brief's "Sem modificar o
 * Core" rule.
 *
 * The storage key prefix is exposed as a constant so tests can
 * inspect it without depending on internals.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import type { FeelingAfter } from './FEELING_AFTER_OPTIONS';
import { isFeelingAfter } from './FEELING_AFTER_OPTIONS';

export const FEEDBACK_STORAGE_PREFIX = 'araflow.feedback.' as const;
const FEEDBACK_LIST_KEY = 'araflow.feedback.index' as const;

export interface FeedbackRecord {
  readonly protocolId: string;
  readonly protocolTitle: string;
  readonly feeling: FeelingAfter;
  readonly sessionDurationMs: number;
  readonly completed: boolean;
  readonly recordedAtIso: string;
}

export interface FeedbackEntry extends FeedbackRecord {
  readonly sessionStartIso: string;
  readonly storageKey: string;
}

export const isFeedbackRecord = (v: unknown): v is FeedbackRecord => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const r = v as Record<string, unknown>;
  return (
    typeof r['protocolId'] === 'string' &&
    typeof r['protocolTitle'] === 'string' &&
    isFeelingAfter(r['feeling']) &&
    typeof r['sessionDurationMs'] === 'number' &&
    typeof r['completed'] === 'boolean' &&
    typeof r['recordedAtIso'] === 'string'
  );
};

/**
 * Build the storage key for a given session start ISO. Sanitizes
 * characters that AsyncStorage does not tolerate (a tiny defensive
 * measure; sessionStartIso is a normal ISO string but the prefix is
 * still applied for safety).
 */
export const buildFeedbackKey = (sessionStartIso: string): string => {
  const sanitized = sessionStartIso.replace(/[^A-Za-z0-9._-]/g, '_');
  return `${FEEDBACK_STORAGE_PREFIX}${sanitized}`;
};

/**
 * Save a feedback record. Returns the resolved storage key on
 * success. Throws on AsyncStorage failure so callers can decide
 * whether to surface the error.
 */
export const saveFeedback = async (
  input: FeedbackRecord & { readonly sessionStartIso: string },
): Promise<FeedbackEntry> => {
  const key = buildFeedbackKey(input.sessionStartIso);
  const entry: FeedbackEntry = Object.freeze({
    ...input,
    storageKey: key,
  });
  const payload = JSON.stringify(entry);
  await AsyncStorage.setItem(key, payload);

  // Maintain a parallel index of all known keys so listFeedback
  // does not have to enumerate the whole store.
  const existing = await AsyncStorage.getItem(FEEDBACK_LIST_KEY);
  const parsed: unknown = existing === null ? [] : JSON.parse(existing);
  const list: string[] = Array.isArray(parsed)
    ? parsed.filter((k): k is string => typeof k === 'string')
    : [];
  if (!list.includes(key)) {
    list.push(key);
    await AsyncStorage.setItem(FEEDBACK_LIST_KEY, JSON.stringify(list));
  }
  return entry;
};

/**
 * Read every feedback entry currently stored. Returns an empty
 * array when nothing is saved. Best-effort: malformed records are
 * silently skipped so a corrupted entry does not break the list.
 */
export const listFeedback = async (): Promise<readonly FeedbackEntry[]> => {
  const indexRaw = await AsyncStorage.getItem(FEEDBACK_LIST_KEY);
  if (indexRaw === null) {
    return Object.freeze([]);
  }
  let keys: string[];
  try {
    const parsed: unknown = JSON.parse(indexRaw);
    keys = Array.isArray(parsed) ? parsed.filter((k): k is string => typeof k === 'string') : [];
  } catch {
    return Object.freeze([]);
  }
  if (keys.length === 0) {
    return Object.freeze([]);
  }
  const pairs = await AsyncStorage.multiGet(keys);
  const out: FeedbackEntry[] = [];
  for (const [k, v] of pairs) {
    if (v === null) {
      continue;
    }
    try {
      const parsed: unknown = JSON.parse(v);
      if (isFeedbackRecord(parsed)) {
        out.push({
          ...parsed,
          sessionStartIso: k.replace(FEEDBACK_STORAGE_PREFIX, ''),
          storageKey: k,
        });
      }
    } catch {
      // Skip malformed entries.
    }
  }
  return Object.freeze(out);
};

/**
 * Remove every feedback entry. Test-only utility — not exposed
 * through the screen.
 */
export const clearAllFeedback = async (): Promise<void> => {
  const indexRaw = await AsyncStorage.getItem(FEEDBACK_LIST_KEY);
  if (indexRaw === null) {
    return;
  }
  try {
    const parsed: unknown = JSON.parse(indexRaw);
    const keys: string[] = Array.isArray(parsed)
      ? parsed.filter((k): k is string => typeof k === 'string')
      : [];
    if (keys.length > 0) {
      await AsyncStorage.multiRemove(keys);
    }
  } finally {
    await AsyncStorage.removeItem(FEEDBACK_LIST_KEY);
  }
};
