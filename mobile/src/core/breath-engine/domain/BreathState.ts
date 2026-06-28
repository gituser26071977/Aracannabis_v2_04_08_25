/**
 * BreathState — máquina de estados do Breath Engine.
 *
 * Estados:
 *   - 'idle'            : engine existe, nenhuma sessão ativa.
 *   - 'preparing'       : contagem regressiva antes do primeiro inhale (opcional).
 *   - 'inhaling'        : inalação ativa.
 *   - 'holdAfterInhale' : retenção após inalação.
 *   - 'exhaling'        : exalação ativa.
 *   - 'holdAfterExhale' : retenção após exalação.
 *   - 'completed'       : todos os ciclos planejados foram concluídos.
 *   - 'cancelled'       : usuário cancelou manualmente.
 *   - 'interrupted'     : app foi para background durante sessão ativa.
 *
 * Diagrama (ASCII):
 *
 *              ┌─────────────┐
 *              │    idle     │ ◄────────────┐
 *              └──────┬──────┘              │
 *                start│                      │ reset
 *                     ▼                      │
 *              ┌─────────────┐               │
 *              │  preparing  │───────────────┤
 *              └──────┬──────┘               │
 *                     │ (prepMs elapses)     │
 *                     ▼                      │
 *              ┌─────────────┐               │
 *              │  inhaling   │               │
 *              └──────┬──────┘               │
 *                     │                      │
 *                     ▼                      │
 *              ┌─────────────┐               │
 *              │holdAfterInh.│               │
 *              └──────┬──────┘               │
 *                     │                      │
 *                     ▼                      │
 *              ┌─────────────┐               │
 *              │  exhaling   │               │
 *              └──────┬──────┘               │
 *                     │                      │
 *                     ▼                      │
 *              ┌─────────────┐               │
 *              │holdAfterExh.│               │
 *              └──────┬──────┘               │
 *                     │                      │
 *          ┌──────────┴──────────┐           │
 *          │                     │           │
 *          ▼                     ▼           │
 *    [inhaling again]      [completed]       │
 *    (more cycles left)     (last cycle done)│
 *                                           │
 *   [cancelled] — called from any active state
 *   [interrupted] — Timer Engine backgrounded event
 *
 * Invariantes:
 *   - `idle` é o único estado em que `start()` é válido.
 *   - Estados ativos (inhaling/holdAfterInhale/exhaling/holdAfterExhale/preparing)
 *     só podem ocorrer após `start()`.
 *   - `completed`, `cancelled`, `interrupted` são terminais — só `reset()` retorna.
 *   - `interrupted` pode voltar a `inhaling` (via foregrounded + resume).
 */

export type BreathState =
  | 'idle'
  | 'preparing'
  | 'inhaling'
  | 'holdAfterInhale'
  | 'exhaling'
  | 'holdAfterExhale'
  | 'completed'
  | 'cancelled'
  | 'interrupted';

export const BREATH_STATES = [
  'idle',
  'preparing',
  'inhaling',
  'holdAfterInhale',
  'exhaling',
  'holdAfterExhale',
  'completed',
  'cancelled',
  'interrupted',
] as const;

export const ACTIVE_BREATH_STATES: readonly BreathState[] = [
  'preparing',
  'inhaling',
  'holdAfterInhale',
  'exhaling',
  'holdAfterExhale',
] as const;

export const TERMINAL_BREATH_STATES: readonly BreathState[] = [
  'completed',
  'cancelled',
] as const;

export const isActiveBreathState = (state: BreathState): boolean =>
  ACTIVE_BREATH_STATES.includes(state);

export const isTerminalBreathState = (state: BreathState): boolean =>
  TERMINAL_BREATH_STATES.includes(state) || state === 'interrupted';