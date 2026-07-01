/**
 * RecoveryDecision — result of a Recovery API call.
 *
 * The Recovery API is explicit: no auto-recovery. Consumers query
 * `canRecover`, then call `recover` (which returns a snapshot) or
 * `discard` (which removes the persisted record).
 */

import type { SessionId } from '@araflow/shared-contracts';

import type { PersistedSessionSnapshot } from './SessionSnapshot';

export type RecoveryReason =
  | 'recoverable' // snapshot exists, decoder compatible
  | 'no-snapshot' // no persisted record for this session
  | 'corrupted' // payload present but invalid
  | 'incompatible' // schema version not supported by current code
  | 'discarded'; // user explicitly discarded

export interface RecoveryProbe {
  readonly sessionId: SessionId;
  readonly canRecover: boolean;
  readonly reason: RecoveryReason;
  readonly snapshotVersion: number | null;
}

export type RecoveryResult =
  | {
      readonly ok: true;
      readonly sessionId: SessionId;
      readonly snapshot: PersistedSessionSnapshot;
      readonly reason: 'recoverable';
    }
  | {
      readonly ok: false;
      readonly sessionId: SessionId;
      readonly reason: Exclude<RecoveryReason, 'recoverable'>;
    };

export const isRecoveryProbe = (v: unknown): v is RecoveryProbe => {
  if (typeof v !== 'object' || v === null) {
    return false;
  }
  const p = v as Partial<RecoveryProbe>;
  return (
    typeof p.sessionId === 'string' &&
    typeof p.canRecover === 'boolean' &&
    typeof p.reason === 'string' &&
    (p.snapshotVersion === null || typeof p.snapshotVersion === 'number')
  );
};
