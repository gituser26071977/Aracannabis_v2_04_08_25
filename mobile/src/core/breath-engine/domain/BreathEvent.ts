/**
 * BreathEvent — eventos emitidos pelo Breath Engine.
 *
 * 9 tipos (8 conforme spec + 1 extensão `resumed-from-interrupt`):
 *
 *   - 'phase-changed'         : mudou de fase (pode ser dentro ou entre ciclos)
 *   - 'cycle-started'         : novo ciclo começou (N=0..cycles-1)
 *   - 'cycle-completed'       : ciclo terminou após holdAfterExhale (N=0..cycles-1)
 *   - 'breath-started'        : sessão inteira começou (uma vez por sessão)
 *   - 'breath-completed'      : uma inalação+exalação terminou (uma vez por ciclo)
 *   - 'completed'             : sessão inteira terminou (uma vez por sessão)
 *   - 'interrupted'           : app foi para background durante sessão ativa
 *   - 'cancelled'             : usuário cancelou manualmente
 *   - 'resumed-from-interrupt': app voltou do background (extensão útil)
 *
 * Semântica das distinções BreathCompleted vs CycleCompleted vs Completed:
 *   - 'breath-completed' : emitido quando a fase exhaling termina (antes de hold).
 *   - 'cycle-completed'  : emitido quando a fase holdAfterExhale termina (fim do ciclo).
 *   - 'completed'        : emitido uma vez no fim da sessão (= mesmo instante do último cycle-completed).
 *
 * Cada evento carrega `monotonicMs`: instante em que o evento foi gerado.
 */

import type { BreathPhase } from './BreathPhase';
import type { BreathState } from './BreathState';

interface BaseEvent {
  readonly monotonicMs: number;
}

export type BreathEvent =
  | (BaseEvent & {
      readonly type: 'phase-changed';
      readonly previousPhase: BreathPhase | null;
      readonly currentPhase: BreathPhase;
      readonly cycleIndex: number;
      readonly phaseProgress: number;
    })
  | (BaseEvent & {
      readonly type: 'cycle-started';
      readonly cycleIndex: number;
      readonly totalCycles: number;
    })
  | (BaseEvent & {
      readonly type: 'cycle-completed';
      readonly cycleIndex: number;
      readonly totalCycles: number;
    })
  | (BaseEvent & {
      readonly type: 'breath-started';
      readonly totalCycles: number;
      readonly totalDurationMs: number;
    })
  | (BaseEvent & {
      readonly type: 'breath-completed';
      readonly cycleIndex: number;
      readonly totalCycles: number;
    })
  | (BaseEvent & {
      readonly type: 'completed';
      readonly totalCycles: number;
      readonly totalElapsedMs: number;
    })
  | (BaseEvent & {
      readonly type: 'interrupted';
      readonly stateBefore: BreathState;
      readonly elapsedAtInterruptionMs: number;
    })
  | (BaseEvent & {
      readonly type: 'resumed-from-interrupt';
      readonly stateBefore: BreathState;
      readonly interruptedForMs: number;
      readonly resumedPhase: BreathPhase | null;
      readonly resumedCycleIndex: number;
    })
  | (BaseEvent & {
      readonly type: 'cancelled';
      readonly stateBefore: BreathState;
      readonly elapsedAtCancelMs: number;
      readonly cyclesCompleted: number;
    });

export const BREATH_EVENT_TYPES = [
  'phase-changed',
  'cycle-started',
  'cycle-completed',
  'breath-started',
  'breath-completed',
  'completed',
  'interrupted',
  'resumed-from-interrupt',
  'cancelled',
] as const;

export type BreathEventType = (typeof BREATH_EVENT_TYPES)[number];