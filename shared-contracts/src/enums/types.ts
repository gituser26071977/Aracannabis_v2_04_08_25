/**
 * CurveFn — function type for curve interpolation.
 *
 * Defined here (in enums/) to avoid circular imports between breath.ts
 * and curves (which would be elsewhere). Curves themselves are
 * registered by name in @core/breath-engine, not in shared-contracts.
 */

export type CurveFn = (progress: number) => number;