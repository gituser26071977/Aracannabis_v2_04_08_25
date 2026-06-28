/**
 * TimerMode — modo de operação do Timer Engine.
 *
 * 'high-precision': 60Hz tick rate. Uso: animações, sync com áudio.
 *   Consome mais CPU, mas jitter mínimo.
 * 'balanced': 10Hz tick rate. Uso: sessão de respiração padrão.
 *   Bom trade-off entre precisão e consumo.
 * 'low-power': 1Hz tick rate. Uso: background tracking.
 *   Mínimo consumo, precisão suficiente para telemetria agregada.
 *
 * Default: 'balanced'.
 *
 * O modo pode ser alterado em runtime. Mudanças não invalidam o
 * estado atual da sessão; apenas ajustam a frequência de tick.
 */

export type TimerMode = 'high-precision' | 'balanced' | 'low-power';

export const TIMER_MODE_TICK_INTERVAL_MS: Readonly<Record<TimerMode, number>> = {
  'high-precision': 1000 / 60, // 16.666... ms
  balanced: 100, // 100 ms
  'low-power': 1000, // 1 s
};

export const DEFAULT_TIMER_MODE: TimerMode = 'balanced';
