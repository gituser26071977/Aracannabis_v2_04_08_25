/**
 * RuntimeEvent — tagged union over all events emitted by the
 * AraFlow Runtime. The 3 frozen Core engines emit their own
 * strongly-typed event unions; the Runtime unifies them under a
 * single `source` discriminant.
 *
 * The Runtime itself contributes a `source: 'runtime'` channel
 * for lifecycle projections (compile-failed, errored, disposed,
 * warnings, completed) that have no equivalent at the engine level.
 */

import type { BreathEvent } from '@core/breath-engine';
import type { ProtocolRuntimeEvent } from '@core/protocol-compiler';
import type { TimerEvent } from '@core/timer-engine';

import type { RuntimeLifecycleEvent } from './RuntimeLifecycleEvent';

export type RuntimeEventSource = 'timer' | 'breath' | 'protocol' | 'runtime';

export type RuntimeEvent =
  | { readonly source: 'timer'; readonly payload: TimerEvent }
  | { readonly source: 'breath'; readonly payload: BreathEvent }
  | { readonly source: 'protocol'; readonly payload: ProtocolRuntimeEvent }
  | { readonly source: 'runtime'; readonly payload: RuntimeLifecycleEvent };

export type RuntimeEventListener = (event: RuntimeEvent) => void;
export type RuntimeUnsubscribe = () => void;

export const RUNTIME_EVENT_SOURCES: readonly RuntimeEventSource[] = [
  'timer',
  'breath',
  'protocol',
  'runtime',
] as const;

export const isRuntimeEventSource = (value: unknown): value is RuntimeEventSource =>
  typeof value === 'string' && (RUNTIME_EVENT_SOURCES as readonly string[]).includes(value);
