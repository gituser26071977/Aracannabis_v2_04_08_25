/**
 * breath.ts — BreathPhase, CurveType, InterpolationType.
 *
 * Coverage:
 *   - BREATH_PHASES, CURVE_TYPES, INTERPOLATION_TYPES tuples
 *   - isBreathPhase, isCurveType, isInterpolationType predicates
 */

import {
  BREATH_PHASES,
  isBreathPhase,
  CURVE_TYPES,
  isCurveType,
  INTERPOLATION_TYPES,
  isInterpolationType,
} from '../../src/enums/breath';

describe('enums/breath', () => {
  describe('BREATH_PHASES', () => {
    it('contains canonical 4 phases', () => {
      expect(BREATH_PHASES).toEqual([
        'inhaling',
        'holdAfterInhale',
        'exhaling',
        'holdAfterExhale',
      ]);
    });
    it('isBreathPhase accepts valid', () => {
      expect(isBreathPhase('inhaling')).toBe(true);
      expect(isBreathPhase('holdAfterInhale')).toBe(true);
      expect(isBreathPhase('exhaling')).toBe(true);
      expect(isBreathPhase('holdAfterExhale')).toBe(true);
    });
    it('isBreathPhase rejects invalid', () => {
      expect(isBreathPhase('inhale')).toBe(false);
      expect(isBreathPhase('hold-in')).toBe(false);
      expect(isBreathPhase('')).toBe(false);
      expect(isBreathPhase(null)).toBe(false);
      expect(isBreathPhase(123)).toBe(false);
    });
  });

  describe('CURVE_TYPES', () => {
    it('contains all 7 curves', () => {
      expect(CURVE_TYPES).toEqual([
        'linear',
        'easeIn',
        'easeOut',
        'easeInOut',
        'sine',
        'cosine',
        'bezier',
      ]);
    });
    it('isCurveType accepts valid', () => {
      for (const c of CURVE_TYPES) {
        expect(isCurveType(c)).toBe(true);
      }
    });
    it('isCurveType rejects invalid', () => {
      expect(isCurveType('unknown')).toBe(false);
      expect(isCurveType(null)).toBe(false);
    });
  });

  describe('INTERPOLATION_TYPES', () => {
    it('contains 3 interpolation types', () => {
      expect(INTERPOLATION_TYPES).toEqual(['discrete', 'linear', 'curve']);
    });
    it('isInterpolationType accepts valid', () => {
      expect(isInterpolationType('discrete')).toBe(true);
      expect(isInterpolationType('linear')).toBe(true);
      expect(isInterpolationType('curve')).toBe(true);
    });
    it('isInterpolationType rejects invalid', () => {
      expect(isInterpolationType('cubic')).toBe(false);
      expect(isInterpolationType(undefined)).toBe(false);
    });
  });
});
