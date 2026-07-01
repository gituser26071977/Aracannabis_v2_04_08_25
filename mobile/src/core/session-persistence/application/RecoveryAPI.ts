/**
 * RecoveryAPI — explicit recovery control surface.
 *
 * Per Sprint 7 brief: NO auto-recovery. Consumers must:
 *   1. Call `canRecover(sessionId)` to probe.
 *   2. Call `recover(sessionId)` to load (returns the snapshot).
 *   3. Call `discard(sessionId)` to remove the persisted record.
 *
 * The API is a thin wrapper over SessionPersistence — it does NOT
 * touch the Session Orchestrator. Building a fresh Session from the
 * snapshot is a Sprint 8 concern (the brief defers it).
 */

import type { SessionId } from '@araflow/shared-contracts';

import type { RecoveryProbe, RecoveryReason, RecoveryResult } from '../domain/RecoveryDecision';
import type { SessionPersistence, LoadFailureReason } from '../domain/SessionPersistence';

/**
 * Map a LoadFailureReason to a RecoveryReason. `not-found` is not a
 * Recovery concern (Recovery is only about existing snapshots), so it
 * maps to `no-snapshot`. `storage-failed` is treated as `corrupted`
 * for the user-facing probe (the payload is unverifiable).
 */
const mapFailureReason = (
  r: LoadFailureReason,
): Exclude<RecoveryReason, 'recoverable' | 'discarded'> => {
  switch (r) {
    case 'not-found':
      return 'no-snapshot';
    case 'corrupted':
      return 'corrupted';
    case 'incompatible':
      return 'incompatible';
    case 'storage-failed':
      return 'corrupted';
  }
};

export const RECOVERY_API_ID = 'recovery-api-v1' as const;

export interface RecoveryAPIDeps {
  readonly persistence: SessionPersistence;
}

export interface RecoveryAPI {
  readonly recoveryId: string;

  /** Probe whether a session can be recovered. Does NOT load the payload. */
  canRecover(sessionId: SessionId): Promise<RecoveryProbe>;

  /** Load the persisted snapshot. */
  recover(sessionId: SessionId): Promise<RecoveryResult>;

  /** Delete the persisted snapshot. */
  discard(sessionId: SessionId): Promise<void>;
}

export const createRecoveryAPI = (deps: RecoveryAPIDeps): RecoveryAPI => ({
  recoveryId: RECOVERY_API_ID,

  async canRecover(sessionId: SessionId): Promise<RecoveryProbe> {
    const exists = await deps.persistence.exists(sessionId);
    if (!exists) {
      return {
        sessionId,
        canRecover: false,
        reason: 'no-snapshot',
        snapshotVersion: null,
      };
    }
    const result = await deps.persistence.load(sessionId);
    if (result.ok) {
      return {
        sessionId,
        canRecover: true,
        reason: 'recoverable',
        snapshotVersion: result.snapshot.metadata.serializerVersion,
      };
    }
    const reason = mapFailureReason(result.reason);
    return {
      sessionId,
      canRecover: false,
      reason,
      snapshotVersion: null,
    };
  },

  async recover(sessionId: SessionId): Promise<RecoveryResult> {
    const result = await deps.persistence.load(sessionId);
    if (result.ok) {
      return {
        ok: true,
        sessionId,
        snapshot: result.snapshot,
        reason: 'recoverable',
      };
    }
    return {
      ok: false,
      sessionId,
      reason: mapFailureReason(result.reason),
    };
  },

  async discard(sessionId: SessionId): Promise<void> {
    await deps.persistence.delete(sessionId);
  },
});
