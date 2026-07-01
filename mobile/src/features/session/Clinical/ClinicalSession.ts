/**
 * ClinicalSession — Sprint 11 end-to-end orchestrator.
 *
 * Wires the entire AraFlow Core for one clinical breathing session:
 *
 *   RuntimeEngine ─┬─ AnimationEngine (drives visual frame)
 *                  ├─ AudioEngine    (InMemoryAudioAdapter)
 *                  └─ SessionOrchestrator
 *                       └─ ExecutionSession (DDD aggregate)
 *
 * PersistenceService is held alongside and is invoked on natural
 * completion to capture a `PersistedSessionSnapshot`. Cancellation
 * does NOT persist; the feedback screen records `completed: false`
 * via FeedbackStorage.
 *
 * Architectural rules (per brief):
 *   - No Core module is modified.
 *   - AudioEngine and AnimationEngine each subscribe to the same
 *     Runtime; Runtime deduplicates the event stream so multiple
 *     subscribers are safe.
 *   - SessionOrchestrator bridges Runtime ↔ ExecutionSession. The
 *     orchestrator is then ATTACHED so events flow.
 *   - The handle exposes a stable status/frame read model so the
 *     screen can drive rAF without depending on engine internals.
 *
 * Lifecycle:
 *
 *   const result = await startClinicalSession({
 *     protocol: entry,
 *     audioAdapter,
 *     storageAdapter,
 *     now: () => Date.now(),
 *     onPersist: async (snapshot) => { ... },
 *   });
 *   if (result.ok) {
 *     const handle = result.value;
 *     handle.start();
 *     // rAF tick reads handle.update()
 *     await handle.stop();
 *   }
 */

import type { EngineId, Result, SessionId } from '@araflow/shared-contracts';
import { EngineError, Err, Ok, SessionId as SessionIdConstructor } from '@araflow/shared-contracts';

import type { AnimationFrame } from '@core/animation-engine';
import { createAnimation } from '@core/animation-engine';
import type { AudioAdapter } from '@core/audio-engine';
import { createAudioEngine } from '@core/audio-engine';
import { ExecutionSession } from '@core/execution-session';
import type {
  PersistedSessionSnapshot,
  SessionPersistence,
  StorageAdapter,
} from '@core/session-persistence';
import {
  createJsonSerializer,
  createMemoryStorageAdapter,
  createPersistenceService,
  sessionToPersistedSnapshot,
} from '@core/session-persistence';
import { SessionOrchestrator } from '@core/session-orchestrator';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import { JsonSource } from '@core/protocol-compiler';
import type { RuntimeEvent } from '@core/runtime';
import { RuntimeEngine } from '@core/runtime';

import type { ClinicalSessionHandle, ClinicalSessionStatus } from './ClinicalSessionHandle';
import type { ClinicalProtocolEntry } from './protocols';

export interface ClinicalSessionOptions {
  readonly protocol: ClinicalProtocolEntry;
  readonly audioAdapter: AudioAdapter;
  readonly storageAdapter?: StorageAdapter;
  readonly now?: () => number;
  /** Callback invoked on natural completion with the persisted snapshot. */
  readonly onPersist?: (snapshot: PersistedSessionSnapshot) => Promise<void> | void;
}

export const CLINICAL_RUNTIME_ID: EngineId = 'araflow-clinical-v1' as EngineId;

const ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

/**
 * Minimal 26-char Crockford-base32 ULID. Pure function over a
 * monotonic time source so tests can drive deterministic ids.
 *
 * Exposed for tests.
 */
export const buildClinicalSessionUlid = (monotonicMs: number, randomTail: number): string => {
  const chars: string[] = new Array(26);
  let t = monotonicMs;
  for (let i = 9; i >= 0; i -= 1) {
    chars[i] = ALPHABET[t % 32] ?? '0';
    t = Math.floor(t / 32);
  }
  let r = randomTail >>> 0;
  for (let i = 25; i >= 10; i -= 1) {
    chars[i] = ALPHABET[r % 32] ?? '0';
    r = Math.floor(r / 32);
  }
  return chars.join('');
};

interface OrchestratorState {
  status: ClinicalSessionStatus;
  frame: AnimationFrame | null;
  startedAtMs: number | null;
  stoppedAtMs: number | null;
  completedNaturally: boolean;
  disposed: boolean;
}

export const startClinicalSession = async (
  options: ClinicalSessionOptions,
): Promise<Result<ClinicalSessionHandle, EngineError>> => {
  const now = options.now ?? ((): number => Date.now());

  // 1. Runtime.
  const runtime = new RuntimeEngine({ runtimeId: CLINICAL_RUNTIME_ID });
  const source = JsonSource(options.protocol.source);
  const compileResult = runtime.compile(source);
  if (!compileResult.ok) {
    return Err(compileResult.error);
  }
  const plan: ProtocolExecutionPlan | null = runtime.getExecutionPlan();
  if (plan === null) {
    return Err(
      new EngineError('clinical-session: protocol plan is null after compile', {
        code: 'runtime_no_plan',
        severity: 'error',
      }),
    );
  }

  // 2. Animation Engine — subscribes to the same Runtime.
  const animation = createAnimation({ runtime });

  // 3. Audio Engine — subscribes to the same Runtime (Sprint 10).
  const audio = createAudioEngine({ runtime, adapter: options.audioAdapter });

  // 4. ExecutionSession (DDD aggregate). Identity is stable for
  //    the lifetime of the session. protocolId comes from the plan.
  const sessionId: SessionId = SessionIdConstructor(
    buildClinicalSessionUlid(now(), (now() * 2654435761) >>> 0),
  );
  const session: ExecutionSession = new ExecutionSession({
    sessionId,
    protocolId: plan.protocolId,
    executionPlanId: plan.executionId as never,
    plan,
    now,
  });

  // 5. SessionOrchestrator — bridge Runtime ↔ ExecutionSession.
  const orchestrator = new SessionOrchestrator({ runtime, session, now });

  // 6. PersistenceService — held for save-on-complete.
  const serializer = createJsonSerializer();
  const storage: StorageAdapter = options.storageAdapter ?? createMemoryStorageAdapter();
  const persistence: SessionPersistence = createPersistenceService({ serializer, storage });

  // 7. Internal state.
  const state: OrchestratorState = {
    status: 'starting',
    frame: null,
    startedAtMs: null,
    stoppedAtMs: null,
    completedNaturally: false,
    disposed: false,
  };

  // 8. Track the latest AnimationFrame via the engine's event stream.
  const animationOff = animation.subscribe((event) => {
    if (event.type === 'animation-frame') {
      state.frame = event.frame;
    }
  });
  animation.start();

  // 9. React to Runtime lifecycle events: completed/cancelled.
  const onRuntimeEvent = (event: RuntimeEvent): void => {
    if (event.source !== 'runtime') {
      return;
    }
    const p = event.payload;
    if (p.type === 'runtime-completed') {
      state.status = 'completed';
      state.completedNaturally = true;
      state.stoppedAtMs = now();
      void persistAndTearDown();
    } else if (p.type === 'runtime-error') {
      state.status = 'errored';
      state.stoppedAtMs = now();
      void tearDown();
    }
  };
  const runtimeOff = runtime.subscribe(onRuntimeEvent);

  // 10. Persist on natural completion, then dispose. Cancellation
  //     does NOT persist (handled in `stop()` directly).
  const persistAndTearDown = async (): Promise<void> => {
    try {
      const snapshot = sessionToPersistedSnapshot({
        session,
        capturedAtMonotonicMs: now(),
        serializerVersion: 1,
        label: `clinical:${options.protocol.id}`,
      });
      const saveResult = await persistence.save({
        sessionId: session.sessionId(),
        snapshot,
        overwrite: true,
      });
      if (saveResult.ok && options.onPersist) {
        await options.onPersist(snapshot);
      }
    } catch {
      // Persistence failure is non-fatal for the user — the session
      // still completed. The screen will still surface feedback.
    } finally {
      tearDown();
    }
  };

  const tearDown = (): void => {
    if (state.disposed) {
      return;
    }
    state.disposed = true;
    animationOff();
    runtimeOff();
    animation.dispose();
    audio.dispose();
    orchestrator.dispose();
    session.dispose();
  };

  // 11. The handle. All methods delegate to the underlying Core
  //     engines; no Core state is owned here.
  const handle: ClinicalSessionHandle = {
    status: (): ClinicalSessionStatus => state.status,
    currentFrame: (): AnimationFrame | null => state.frame,
    update: (): AnimationFrame | null => {
      if (state.disposed) {
        return state.frame;
      }
      const next = animation.update(now());
      state.frame = next;
      return next;
    },
    remainingMs: (): number => state.frame?.remainingTime ?? 0,
    totalDurationMs: (): number => (plan.totalDuration as unknown as number) ?? 0,
    protocolTitle: (): string => plan.title,
    protocolId: (): string => plan.protocolId,
    startedAtIso: (): string | null =>
      state.startedAtMs === null ? null : new Date(state.startedAtMs).toISOString(),
    completedNaturally: (): boolean => state.completedNaturally,
    start: (): void => {
      if (state.status !== 'starting' && state.status !== 'idle') {
        return;
      }
      state.startedAtMs = now();
      state.status = 'running';
      const r = runtime.start();
      if (!r.ok) {
        state.status = 'errored';
        return;
      }
      // Attach the orchestrator AFTER runtime.start so the session
      // picks up phase changes from the first cycle onward.
      const attach = orchestrator.attach();
      if (!attach.ok) {
        state.status = 'errored';
      }
    },
    pause: (): void => {
      if (state.status !== 'running') {
        return;
      }
      const r = runtime.pause();
      if (r.ok) {
        state.status = 'paused';
        animation.pause();
      }
    },
    resume: (): void => {
      if (state.status !== 'paused') {
        return;
      }
      const r = runtime.resume();
      if (r.ok) {
        state.status = 'running';
        animation.resume();
      }
    },
    stop: async (): Promise<void> => {
      if (
        state.status === 'completed' ||
        state.status === 'cancelled' ||
        state.status === 'errored' ||
        state.status === 'disposed'
      ) {
        tearDown();
        return;
      }
      const r = runtime.cancel();
      void r;
      state.status = 'cancelled';
      state.completedNaturally = false;
      state.stoppedAtMs = now();
      // Cancellation: do NOT persist a snapshot. The screen will
      // still surface the feedback screen so the user can mark
      // the session as cancelled.
      tearDown();
    },
    dispose: async (): Promise<void> => {
      tearDown();
    },
  };

  return Ok(handle);
};

// Re-export the handle types so consumers can `import { ClinicalSessionHandle } from '../ClinicalSession'`
// without depending on a second path.
export type { ClinicalSessionHandle, ClinicalSessionStatus } from './ClinicalSessionHandle';
