/**
 * UUID generation and validation.
 *
 * Provides a pure-JS UUID v4 generator that doesn't depend on Node's
 * `crypto` module or the browser's `crypto.randomUUID`. Useful for
 * environments where those are unavailable.
 */

import { AppError } from '../value-objects/validation';
import { UUID_V4_PATTERN, isNonEmptyString } from '../value-objects/validation';

const HEX = '0123456789abcdef';

/**
 * Generates a random UUID v4 string using Math.random.
 *
 * NOT cryptographically secure. Use Node's `crypto.randomUUID()` or
 * `crypto.getRandomValues()` in production for security-sensitive IDs.
 */
export const generateUuidV4 = (): string => {
  const bytes = new Array<number>(16);
  for (let i = 0; i < 16; i += 1) {
    bytes[i] = Math.floor(Math.random() * 256);
  }
  // Version 4: high nibble of byte 6 = 0100
  bytes[6] = (bytes[6]! & 0x0f) | 0x40;
  // Variant 10xx: high two bits of byte 8 = 10
  bytes[8] = (bytes[8]! & 0x3f) | 0x80;

  const hex: string[] = [];
  for (let i = 0; i < 16; i += 1) {
    const b = bytes[i]!;
    const hi = HEX[(b >> 4) & 0x0f]!;
    const lo = HEX[b & 0x0f]!;
    hex.push(hi + lo);
  }
  return (
    `${hex.slice(0, 4).join('')}-` +
    `${hex.slice(4, 6).join('')}-` +
    `${hex.slice(6, 8).join('')}-` +
    `${hex.slice(8, 10).join('')}-` +
    `${hex.slice(10, 16).join('')}`
  );
};

/**
 * Validates that a string is a UUID v4. Throws on invalid.
 */
export const validateUuidV4 = (raw: string): void => {
  if (!isNonEmptyString(raw) || !UUID_V4_PATTERN.test(raw)) {
    throw new AppError('Invalid UUID v4 format', {
      code: 'invalid_uuid_v4',
      severity: 'warn',
      context: { raw },
    });
  }
};

/**
 * Generates a ULID-like 26-char Crockford Base32 string.
 * Sortable lexicographically (timestamp prefix).
 *
 * NOT cryptographically secure. For real ULIDs use a dedicated library.
 */
export const generateUlidLike = (timestamp: number = Date.now()): string => {
  const CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
  const timeChars: string[] = [];
  let t = timestamp;
  for (let i = 9; i >= 0; i -= 1) {
    const mod = t % 32;
    timeChars[i] = CROCKFORD[mod]!;
    t = Math.floor(t / 32);
  }
  const randomChars: string[] = [];
  for (let i = 0; i < 16; i += 1) {
    randomChars.push(CROCKFORD[Math.floor(Math.random() * 32)]!);
  }
  return timeChars.join('') + randomChars.join('');
};