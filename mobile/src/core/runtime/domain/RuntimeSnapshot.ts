/**
 * RuntimeSnapshot — point-in-time view of the entire Runtime facade.
 *
 * Combines the Runtime-level state with the underlying engine
 * snapshots (TimerEngineSnapshot, BreathSnapshot, ProtocolRuntimeSnapshot)
 * and the loaded plan reference.
 *
 * Consumers that want a single read call instead of fanning out to
 * three engines get this shape.
 */

import type { EngineId } from '@araflow/shared-contracts';

import type { BreathSnapshot } from '@core/breath-engine';
import type { ProtocolExecutionPlan, ProtocolRuntimeSnapshot } from '@core/protocol-compiler';
import type { TimerEngineSnapshot } from '@core/timer-engine';

import type { RuntimeState } from './RuntimeState';

export interface RuntimeSnapshot {
  readonly runtimeId: EngineId;
  readonly state: RuntimeState;
  readonly plan: ProtocolExecutionPlan | null;
  readonly protocol: ProtocolRuntimeSnapshot | null;
  readonly breath: BreathSnapshot | null;
  readonly timer: TimerEngineSnapshot | null;
}
