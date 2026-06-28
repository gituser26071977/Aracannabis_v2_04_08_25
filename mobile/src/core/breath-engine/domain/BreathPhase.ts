/**
 * BreathPhase — uma única fase dentro de um ciclo respiratório.
 *
 * O Breath Engine conhece APENAS quatro fases mecânicas:
 *   - 'inhaling'         : ar entrando nos pulmões
 *   - 'holdAfterInhale'  : ar retido após inalação completa
 *   - 'exhaling'         : ar saindo dos pulmões
 *   - 'holdAfterExhale'  : pulmões vazios, em pausa antes da próxima inalação
 *
 * IMPORTANTE: estas fases NÃO carregam significado clínico. Box Breathing,
 * Coherent Breathing, 4-7-8, etc. são protocolos (responsabilidade do
 * Protocol Engine) e são expressos como combinação de durações nestas
 * quatro fases.
 *
 * Invariantes:
 *   - Ordem obrigatória: inhaling → holdAfterInhale → exhaling → holdAfterExhale → inhaling ...
 *   - Cada fase tem duração configurável (pode ser zero).
 *   - Phase progress é sempre em [0, 1] dentro da fase atual.
 */

export type BreathPhase = 'inhaling' | 'holdAfterInhale' | 'exhaling' | 'holdAfterExhale';

export const BREATH_PHASES = ['inhaling', 'holdAfterInhale', 'exhaling', 'holdAfterExhale'] as const;

export const BREATH_PHASE_ORDER: readonly BreathPhase[] = [
  'inhaling',
  'holdAfterInhale',
  'exhaling',
  'holdAfterExhale',
] as const;

/**
 * Returns the phase that follows the given phase in a breath cycle.
 * After holdAfterExhale, the cycle wraps back to inhaling.
 */
export const nextPhase = (phase: BreathPhase): BreathPhase => {
  switch (phase) {
    case 'inhaling':
      return 'holdAfterInhale';
    case 'holdAfterInhale':
      return 'exhaling';
    case 'exhaling':
      return 'holdAfterExhale';
    case 'holdAfterExhale':
      return 'inhaling';
  }
};