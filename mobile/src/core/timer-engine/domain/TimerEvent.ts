/**
 * TimerEvent — eventos emitidos pelo Timer Engine.
 *
 * Eventos são union discriminada por `type`. Consumers devem
 * usar exhaustive switch (assertNever) para garantir tratamento
 * completo em compile time.
 *
 * Cada evento carrega:
 *   - monotonicMs: instante em que o evento foi gerado (monotônico).
 *   - wallIso: instante em ISO 8601 (para logs/serialização).
 *   - payload: dados específicos do evento.
 */

import type { DriftMeasurement } from './DriftMeasurement';
import type { TimerMode } from './TimerMode';
import type { TimerState } from './TimerState';

interface BaseEvent {
  readonly monotonicMs: number;
  readonly wallIso: string;
}

export type TimerEvent =
  | (BaseEvent & {
      readonly type: 'started';
      readonly startMonotonicMs: number;
      readonly startWallIso: string;
    })
  | (BaseEvent & {
      readonly type: 'paused';
      readonly totalElapsedMs: number;
      readonly pausedAtMonotonicMs: number;
    })
  | (BaseEvent & {
      readonly type: 'resumed';
      readonly totalElapsedMs: number;
      readonly pausedForMs: number;
    })
  | (BaseEvent & {
      readonly type: 'stopped';
      readonly totalElapsedMs: number;
      readonly totalActiveMs: number;
    })
  | (BaseEvent & {
      readonly type: 'reset';
      readonly previousState: TimerState;
    })
  | (BaseEvent & {
      readonly type: 'tick';
      readonly tickIndex: number;
      readonly elapsedMs: number;
      readonly totalElapsedMs: number;
    })
  | (BaseEvent & {
      readonly type: 'drift';
      readonly measurement: DriftMeasurement;
    })
  | (BaseEvent & {
      readonly type: 'mode-changed';
      readonly previousMode: TimerMode;
      readonly currentMode: TimerMode;
      readonly tickIntervalMs: number;
    })
  | (BaseEvent & {
      readonly type: 'backgrounded';
      readonly totalElapsedMs: number;
    })
  | (BaseEvent & {
      readonly type: 'foregrounded';
      readonly totalElapsedMs: number;
      readonly backgroundedForMs: number;
    })
  | (BaseEvent & {
      readonly type: 'time-scale-changed';
      readonly previousScale: number;
      readonly currentScale: number;
    });

export const TIMER_EVENT_TYPES = [
  'started',
  'paused',
  'resumed',
  'stopped',
  'reset',
  'tick',
  'drift',
  'mode-changed',
  'backgrounded',
  'foregrounded',
  'time-scale-changed',
] as const;

export type TimerEventType = (typeof TIMER_EVENT_TYPES)[number];
