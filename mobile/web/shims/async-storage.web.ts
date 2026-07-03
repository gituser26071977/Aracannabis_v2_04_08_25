/**
 * AraFlow — AsyncStorage shim for web.
 *
 * `react-native-async-storage` ships a native-only implementation. On
 * web we route every call to `localStorage` so the Clinical MVP feedback
 * store continues to work in the browser.
 *
 * The shim is intentionally minimal — it implements only the surface
 * the app uses (`getItem`, `setItem`, `removeItem`, `multiGet`,
 * `multiRemove`, `clear`). Methods return `Promise`s to match the
 * native contract.
 */

type StorageKey = string;

const NS = 'araflow.as.';

const k = (key: StorageKey): StorageKey => `${NS}${key}`;

export const getItem = async (key: StorageKey): Promise<string | null> => {
  try {
    return window.localStorage.getItem(k(key));
  } catch {
    return null;
  }
};

export const setItem = async (key: StorageKey, value: string): Promise<void> => {
  try {
    window.localStorage.setItem(k(key), value);
  } catch {
    // QuotaExceededError etc. — fail silent per native AsyncStorage.
  }
};

export const removeItem = async (key: StorageKey): Promise<void> => {
  try {
    window.localStorage.removeItem(k(key));
  } catch {
    /* noop */
  }
};

export const multiGet = async (
  keys: readonly StorageKey[],
): Promise<readonly [StorageKey, string | null][]> => {
  return Promise.all(keys.map(async (key) => [key, await getItem(key)] as const));
};

export const multiRemove = async (keys: readonly StorageKey[]): Promise<void> => {
  await Promise.all(keys.map(removeItem));
};

export const clear = async (): Promise<void> => {
  try {
    const toRemove: StorageKey[] = [];
    for (let i = 0; i < window.localStorage.length; i += 1) {
      const key = window.localStorage.key(i);
      if (key !== null && key.startsWith(NS)) {
        toRemove.push(key);
      }
    }
    toRemove.forEach((key) => window.localStorage.removeItem(key));
  } catch {
    /* noop */
  }
};

const AsyncStorage = {
  getItem,
  setItem,
  removeItem,
  multiGet,
  multiRemove,
  clear,
};

export default AsyncStorage;
