/**
 * SessionEventLog — append-only immutable event log.
 *
 * Stored internally as a frozen array. Every append produces a new
 * frozen array; the old array is preserved (snapshot semantics) so
 * callers can compare versions.
 *
 * `append` is the only mutating operation; `all` and `last` are pure.
 */

import type { SessionEvent } from '../domain/SessionEvent';

export class SessionEventLog {
  private entries: readonly SessionEvent[] = Object.freeze([]);

  public append(event: SessionEvent): void {
    this.entries = Object.freeze([...this.entries, event]);
  }

  public all(): readonly SessionEvent[] {
    return this.entries;
  }

  public size(): number {
    return this.entries.length;
  }

  public last(): SessionEvent | null {
    const e = this.entries[this.entries.length - 1];
    return e ?? null;
  }

  public at(index: number): SessionEvent | null {
    if (index < 0 || index >= this.entries.length) {
      return null;
    }
    return this.entries[index] ?? null;
  }

  public clear(): void {
    this.entries = Object.freeze([]);
  }
}
