/**
 * DocumentCurve — exhaustive tests for the document ↔ canonical curve mapping.
 */

import {
  DOCUMENT_CURVE_TYPES,
  DocumentCurveType,
  isDocumentCurveType,
  toCanonicalCurve,
  fromCanonicalCurve,
  isCanonicalCurve,
} from '../../../../src/core/protocol-compiler/domain/DocumentCurve';

describe('DocumentCurve', () => {
  describe('DOCUMENT_CURVE_TYPES', () => {
    it('contains all seven canonical curve names', () => {
      expect(DOCUMENT_CURVE_TYPES).toEqual([
        'linear',
        'ease-in',
        'ease-out',
        'ease-in-out',
        'sine',
        'cosine',
        'bezier',
      ]);
    });
  });

  describe('isDocumentCurveType', () => {
    it('returns true for each document curve type', () => {
      for (const c of DOCUMENT_CURVE_TYPES) {
        expect(isDocumentCurveType(c)).toBe(true);
      }
    });

    it('returns false for canonical names', () => {
      expect(isDocumentCurveType('easeIn')).toBe(false);
      expect(isDocumentCurveType('easeOut')).toBe(false);
      expect(isDocumentCurveType('easeInOut')).toBe(false);
    });

    it('returns false for non-strings', () => {
      expect(isDocumentCurveType(123)).toBe(false);
      expect(isDocumentCurveType(null)).toBe(false);
      expect(isDocumentCurveType(undefined)).toBe(false);
      expect(isDocumentCurveType([])).toBe(false);
    });
  });

  describe('toCanonicalCurve', () => {
    it.each([
      ['linear', 'linear'],
      ['ease-in', 'easeIn'],
      ['ease-out', 'easeOut'],
      ['ease-in-out', 'easeInOut'],
      ['sine', 'sine'],
      ['cosine', 'cosine'],
      ['bezier', 'bezier'],
    ] as Array<[DocumentCurveType, string]>)(
      'maps "%s" → "%s"',
      (doc, canonical) => {
        expect(toCanonicalCurve(doc)).toBe(canonical);
      },
    );

    it('throws on unknown document curve', () => {
      expect(() => toCanonicalCurve('unknown' as DocumentCurveType)).toThrow();
    });
  });

  describe('fromCanonicalCurve', () => {
    it.each([
      ['linear', 'linear'],
      ['easeIn', 'ease-in'],
      ['easeOut', 'ease-out'],
      ['easeInOut', 'ease-in-out'],
      ['sine', 'sine'],
      ['cosine', 'cosine'],
      ['bezier', 'bezier'],
    ] as Array<[string, DocumentCurveType]>)(
      'maps "%s" → "%s"',
      (canonical, doc) => {
        expect(fromCanonicalCurve(canonical as never)).toBe(doc);
      },
    );

    it('throws on unknown canonical curve', () => {
      expect(() => fromCanonicalCurve('unknown' as never)).toThrow();
    });
  });

  describe('round-trip', () => {
    it('preserves identity through both mappings', () => {
      for (const c of DOCUMENT_CURVE_TYPES) {
        expect(fromCanonicalCurve(toCanonicalCurve(c))).toBe(c);
      }
    });
  });

  describe('isCanonicalCurve', () => {
    it('returns true for canonical curves', () => {
      expect(isCanonicalCurve('linear')).toBe(true);
      expect(isCanonicalCurve('easeIn')).toBe(true);
      expect(isCanonicalCurve('sine')).toBe(true);
    });

    it('returns false for document curves', () => {
      expect(isCanonicalCurve('ease-in')).toBe(false);
    });

    it('returns false for non-strings', () => {
      expect(isCanonicalCurve(null)).toBe(false);
      expect(isCanonicalCurve(123)).toBe(false);
    });
  });
});