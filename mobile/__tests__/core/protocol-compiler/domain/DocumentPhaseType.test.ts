/**
 * DocumentPhaseType — exhaustive tests for the document → canonical phase mapping.
 */

import {
  DOCUMENT_PHASE_TYPES,
  DocumentPhaseType,
  isDocumentPhaseType,
  toCanonicalPhase,
  fromCanonicalPhase,
} from '../../../../src/core/protocol-compiler/domain/DocumentPhaseType';

describe('DocumentPhaseType', () => {
  describe('DOCUMENT_PHASE_TYPES', () => {
    it('contains exactly the four canonical names', () => {
      expect(DOCUMENT_PHASE_TYPES).toEqual(['inhale', 'hold-in', 'exhale', 'hold-out']);
    });
  });

  describe('isDocumentPhaseType', () => {
    it('returns true for each document phase type', () => {
      for (const t of DOCUMENT_PHASE_TYPES) {
        expect(isDocumentPhaseType(t)).toBe(true);
      }
    });

    it('returns false for the canonical phase names', () => {
      expect(isDocumentPhaseType('inhaling')).toBe(false);
      expect(isDocumentPhaseType('holdAfterInhale')).toBe(false);
    });

    it('returns false for non-strings', () => {
      expect(isDocumentPhaseType(42)).toBe(false);
      expect(isDocumentPhaseType(null)).toBe(false);
      expect(isDocumentPhaseType(undefined)).toBe(false);
      expect(isDocumentPhaseType({})).toBe(false);
    });

    it('returns false for empty string', () => {
      expect(isDocumentPhaseType('')).toBe(false);
    });
  });

  describe('toCanonicalPhase', () => {
    it('maps inhale → inhaling', () => {
      expect(toCanonicalPhase('inhale')).toBe('inhaling');
    });

    it('maps hold-in → holdAfterInhale', () => {
      expect(toCanonicalPhase('hold-in')).toBe('holdAfterInhale');
    });

    it('maps exhale → exhaling', () => {
      expect(toCanonicalPhase('exhale')).toBe('exhaling');
    });

    it('maps hold-out → holdAfterExhale', () => {
      expect(toCanonicalPhase('hold-out')).toBe('holdAfterExhale');
    });

    it('throws on unknown document phase', () => {
      expect(() => toCanonicalPhase('unknown' as DocumentPhaseType)).toThrow();
    });
  });

  describe('fromCanonicalPhase', () => {
    it('maps inhaling → inhale', () => {
      expect(fromCanonicalPhase('inhaling')).toBe('inhale');
    });

    it('maps holdAfterInhale → hold-in', () => {
      expect(fromCanonicalPhase('holdAfterInhale')).toBe('hold-in');
    });

    it('maps exhaling → exhale', () => {
      expect(fromCanonicalPhase('exhaling')).toBe('exhale');
    });

    it('maps holdAfterExhale → hold-out', () => {
      expect(fromCanonicalPhase('holdAfterExhale')).toBe('hold-out');
    });

    it('round-trips all four types', () => {
      for (const t of DOCUMENT_PHASE_TYPES) {
        expect(fromCanonicalPhase(toCanonicalPhase(t))).toBe(t);
      }
    });
  });
});