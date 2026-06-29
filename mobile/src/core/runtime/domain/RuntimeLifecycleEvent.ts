/**
 * RuntimeLifecycleEvent — events emitted BY the Runtime itself
 * (not by the underlying engines). These live alongside the engine
 * events in the unified RuntimeEvent stream.
 */

import type { Failure } from '@araflow/shared-contracts';

export type RuntimeLifecycleEvent =
  | {
      readonly type: 'runtime-warnings';
      readonly warnings: readonly Failure[];
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'runtime-compile-failed';
      readonly failures: readonly Failure[];
      readonly warnings: readonly Failure[];
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'runtime-error';
      readonly code: string;
      readonly message: string;
      readonly cause?: unknown;
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'runtime-disposed';
      readonly monotonicMs: number;
    }
  | {
      readonly type: 'runtime-completed';
      readonly totalElapsedMs: number;
      readonly monotonicMs: number;
    };

export type RuntimeLifecycleEventType = RuntimeLifecycleEvent['type'];

export const RUNTIME_LIFECYCLE_EVENT_TYPES: readonly RuntimeLifecycleEventType[] = [
  'runtime-warnings',
  'runtime-compile-failed',
  'runtime-error',
  'runtime-disposed',
  'runtime-completed',
] as const;

export const isRuntimeLifecycleEventType = (value: unknown): value is RuntimeLifecycleEventType =>
  typeof value === 'string' && (RUNTIME_LIFECYCLE_EVENT_TYPES as readonly string[]).includes(value);
