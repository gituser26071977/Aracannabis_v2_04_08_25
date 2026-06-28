/**
 * TimeScale — fator de escala entre tempo real e tempo de engine.
 *
 * scale = 1.0  : 1ms real = 1ms engine (uso normal).
 * scale = 0.5  : 1ms real = 0.5ms engine (tempo passa mais devagar).
 * scale = 2.0  : 1ms real = 2ms engine (tempo passa 2x mais rápido).
 * scale = 100  : 1ms real = 100ms engine (testes rápidos: 20min em 12s).
 *
 * Usado por testes e por demos para acelerar/reduzir tempo de
 * validação. NÃO tem efeito sobre a percepção do usuário
 * (sempre é escala 1.0 em produção).
 *
 * Limites práticos:
 *   - Mínimo: 0.001 (1ms real = 1µs engine — efetivamente congelado).
 *   - Máximo: 1000 (1ms real = 1s engine).
 *
 * Valores fora da faixa são rejeitados pelo TimerEngine.setTimeScale.
 */

export const MIN_TIME_SCALE = 0.001;
export const MAX_TIME_SCALE = 1000;
export const DEFAULT_TIME_SCALE = 1;

export const isValidTimeScale = (value: number): boolean => {
  return Number.isFinite(value) && value >= MIN_TIME_SCALE && value <= MAX_TIME_SCALE;
};
