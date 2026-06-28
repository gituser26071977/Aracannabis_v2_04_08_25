/**
 * IntermediateRepresentation — IR helper tests.
 */

import {
  emptyMetadataIR,
  emptyPhaseIR,
  computeCycleIndex,
} from '../../../../src/core/protocol-compiler/domain/IntermediateRepresentation';

describe('IntermediateRepresentation', () => {
  describe('emptyMetadataIR', () => {
    it('returns a metadata object with empty arrays', () => {
      const md = emptyMetadataIR();
      expect(md.references).toEqual([]);
      expect(md.contraindications).toEqual([]);
      expect(md.tags).toEqual([]);
    });
  });

  describe('emptyPhaseIR', () => {
    it('returns a baseline phase', () => {
      const p = emptyPhaseIR();
      expect(p.index).toBe(0);
      expect(p.phase).toBe('inhaling');
      expect(p.duration).toBe(0);
      expect(p.curve).toBe('linear');
      expect(p.ratio).toBe(0);
    });
  });

  describe('computeCycleIndex', () => {
    it('returns 0 for negative numbers', () => {
      expect(computeCycleIndex(-1)).toBe(0);
    });

    it('returns 0 for non-integers', () => {
      expect(computeCycleIndex(1.5)).toBe(0);
    });

    it('returns the value for non-negative integers', () => {
      expect(computeCycleIndex(0)).toBe(0);
      expect(computeCycleIndex(5)).toBe(5);
    });
  });
});