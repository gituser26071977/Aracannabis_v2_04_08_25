/**
 * types.ts — CurveFn type alias.
 *
 * Since CurveFn is purely a type, we test compile-time compatibility.
 */

import type { CurveFn } from '../../src/enums/types';

describe('enums/types', () => {
  describe('CurveFn', () => {
    it('accepts identity-style function', () => {
      const linear: CurveFn = (progress) => progress;
      expect(linear(0.5)).toBe(0.5);
    });
    it('accepts clamping function', () => {
      const clamp: CurveFn = (progress) => Math.max(0, Math.min(1, progress));
      expect(clamp(2)).toBe(1);
      expect(clamp(-1)).toBe(0);
    });
    it('accepts sine-shaped function', () => {
      const sine: CurveFn = (progress) => Math.sin(progress * Math.PI);
      expect(sine(0)).toBe(0);
      expect(sine(1)).toBeCloseTo(0, 5);
    });
  });
});
