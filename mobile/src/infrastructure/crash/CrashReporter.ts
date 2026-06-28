/**
 * Crash Reporter — interface only.
 *
 * Implementation: Sentry (@sentry/react-native) — to be wired in
 * Sprint 7 (observability).
 */

import { AppError } from '@shared/errors';

export interface CrashReporter {
  captureException(error: Error | AppError, context?: Readonly<Record<string, unknown>>): void;
  captureMessage(message: string, level?: 'info' | 'warning' | 'error'): void;
  setUser(userId: string, tenantId: string): void;
  clearUser(): void;
  setTag(key: string, value: string): void;
  addBreadcrumb(category: string, message: string, data?: Readonly<Record<string, unknown>>): void;
}

export class NoopCrashReporter implements CrashReporter {
  public captureException(_error: Error | AppError, _context?: Readonly<Record<string, unknown>>): void {
    // no-op
  }
  public captureMessage(_message: string, _level?: 'info' | 'warning' | 'error'): void {
    // no-op
  }
  public setUser(_userId: string, _tenantId: string): void {
    // no-op
  }
  public clearUser(): void {
    // no-op
  }
  public setTag(_key: string, _value: string): void {
    // no-op
  }
  public addBreadcrumb(
    _category: string,
    _message: string,
    _data?: Readonly<Record<string, unknown>>,
  ): void {
    // no-op
  }
}
