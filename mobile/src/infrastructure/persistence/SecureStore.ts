/**
 * Persistence — SecureStore interface only.
 *
 * Encrypted storage for tokens, biometric refs, and other sensitive
 * data. Implementation: Keychain (iOS) / EncryptedSharedPreferences
 * (Android).
 */

export interface SecureStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
  hasKey(key: string): Promise<boolean>;
}
