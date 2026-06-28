/**
 * Curve — função pura de interpolação no intervalo [0, 1].
 *
 * Recebe um progresso linear (tempo decorrido / duração total da fase) e
 * retorna um valor escalado, tipicamente também em [0, 1]. Esta função é
 * aplicada a cada tick para calcular a "profundidade" da respiração.
 *
 * Arquitetura extensível:
 *   - Implementar a interface `CurveFn` para criar curva customizada.
 *   - Registrar no `curves/index.ts` para descoberta.
 *   - Engines consumidores escolhem curva via string (CurveName) ou
 *     injetam instância diretamente.
 *
 * Garantias:
 *   - f(0) deve ser 0 (exceto em curvas com offset explícito).
 *   - f(1) deve ser 1.
 *   - Sem side effects. Pura. Determinística.
 *   - Pode ser chamada 60Hz sem degradar performance.
 */

export type CurveFn = (progress: number) => number;

export type CurveName =
  | 'linear'
  | 'easeIn'
  | 'easeOut'
  | 'easeInOut'
  | 'sine'
  | 'cosine'
  | 'bezier';

export const CURVE_NAMES: readonly CurveName[] = [
  'linear',
  'easeIn',
  'easeOut',
  'easeInOut',
  'sine',
  'cosine',
  'bezier',
] as const;

export const DEFAULT_CURVE_NAME: CurveName = 'easeInOut';

/**
 * Returns a curve function by name. Throws AppError if name unknown.
 * Consumers can also import curves directly (e.g., `linearCurve`) and
 * bypass this lookup for compile-time safety.
 */
import { AppError } from '@shared/errors';

import { bezierCurve } from './curves/bezier';
import { cosineCurve } from './curves/cosine';
import { easeInCurve } from './curves/easeIn';
import { easeInOutCurve } from './curves/easeInOut';
import { easeOutCurve } from './curves/easeOut';
import { linearCurve } from './curves/linear';
import { sineCurve } from './curves/sine';

const CURVE_REGISTRY: Record<CurveName, CurveFn> = {
  linear: linearCurve,
  easeIn: easeInCurve,
  easeOut: easeOutCurve,
  easeInOut: easeInOutCurve,
  sine: sineCurve,
  cosine: cosineCurve,
  bezier: bezierCurve,
};

export const resolveCurve = (name: CurveName): CurveFn => {
  const curve = CURVE_REGISTRY[name];
  if (curve === undefined) {
    throw new AppError(`Unknown curve name: ${name}`, {
      code: 'breath_unknown_curve',
      severity: 'warn',
      context: { name },
    });
  }
  return curve;
};