/**
 * Document curve — names used in the JSON document.
 *
 * The JSON format uses kebab-case names ('ease-in', 'ease-out') for
 * readability. Shared-contracts uses camelCase ('easeIn', 'easeOut').
 * This module maps between the two.
 */

import { type CurveType, CURVE_TYPES } from '@araflow/shared-contracts';

export const DOCUMENT_CURVE_TYPES = [
  'linear',
  'ease-in',
  'ease-out',
  'ease-in-out',
  'sine',
  'cosine',
  'bezier',
] as const;

export type DocumentCurveType = (typeof DOCUMENT_CURVE_TYPES)[number];

export const isDocumentCurveType = (
  v: unknown,
): v is DocumentCurveType =>
  typeof v === 'string' &&
  (DOCUMENT_CURVE_TYPES as readonly string[]).includes(v);

export const toCanonicalCurve = (doc: DocumentCurveType): CurveType => {
  switch (doc) {
    case 'linear':
      return 'linear';
    case 'ease-in':
      return 'easeIn';
    case 'ease-out':
      return 'easeOut';
    case 'ease-in-out':
      return 'easeInOut';
    case 'sine':
      return 'sine';
    case 'cosine':
      return 'cosine';
    case 'bezier':
      return 'bezier';
    default:
      throw new Error(`Unknown document curve type: ${String(doc)}`);
  }
};

export const fromCanonicalCurve = (curve: CurveType): DocumentCurveType => {
  switch (curve) {
    case 'linear':
      return 'linear';
    case 'easeIn':
      return 'ease-in';
    case 'easeOut':
      return 'ease-out';
    case 'easeInOut':
      return 'ease-in-out';
    case 'sine':
      return 'sine';
    case 'cosine':
      return 'cosine';
    case 'bezier':
      return 'bezier';
    default:
      throw new Error(`Unknown canonical CurveType: ${String(curve)}`);
  }
};

/**
 * Returns true if curve value is a valid canonical CurveType from
 * shared-contracts.
 */
export const isCanonicalCurve = (v: unknown): v is CurveType =>
  typeof v === 'string' && (CURVE_TYPES as readonly string[]).includes(v);
