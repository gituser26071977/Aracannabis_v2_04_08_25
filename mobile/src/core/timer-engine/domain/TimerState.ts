/**
 * TimerState — máquina de estados do Timer Engine.
 *
 * Estados:
 *   - 'idle'      : estado inicial. Engine existe mas não está contando.
 *   - 'running'   : contando. Tick events são emitidos.
 *   - 'paused'    : congelado. Sem ticks. Pode retomar.
 *   - 'stopped'   : terminal. Sessão terminou. Pode apenas ser resetada.
 *
 * Transições válidas:
 *   idle     → running   (start)
 *   running  → paused    (pause)
 *   paused   → running   (resume)
 *   running  → stopped   (stop)
 *   paused   → stopped   (stop)
 *   stopped  → idle      (reset)
 *   running  → idle      (reset)
 *   paused   → idle      (reset)
 *
 * Invariantes:
 *   - Apenas `running` emite tick events.
 *   - `stopped` é terminal exceto via reset.
 *   - `idle` é o único estado em que start() é válido.
 *   - Após reset, todo estado acumulado é zerado.
 *
 * Diagrama (ASCII):
 *
 *          ┌─────────────┐
 *          │    idle     │ ◄────────────────┐
 *          └──────┬──────┘                  │
 *            start│                          │ reset
 *                 ▼                          │
 *          ┌─────────────┐                  │
 *          │   running   │ ──stop──► ┌─────────────┐
 *          └──────┬──────┘           │   stopped   │ ─reset──► idle
 *            pause│  resume          └─────────────┘
 *                 ▼
 *          ┌─────────────┐
 *          │   paused    │
 *          └─────────────┘
 */

export type TimerState = 'idle' | 'running' | 'paused' | 'stopped';

export const TIMER_STATES = ['idle', 'running', 'paused', 'stopped'] as const;
