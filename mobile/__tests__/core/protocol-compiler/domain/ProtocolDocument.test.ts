/**
 * ProtocolDocument — shape checks and helpers.
 */

import {
  computeDeclaredCycleMs,
  computeDeclaredSessionMs,
  DocumentPhase,
  EVIDENCE_LEVELS,
  hasMetadata,
  isEvidenceLevel,
  isProtocolDocumentShape,
} from '../../../../src/core/protocol-compiler/domain/ProtocolDocument';
import { ProtocolId } from '@araflow/shared-contracts';

describe('ProtocolDocument', () => {
  describe('EVIDENCE_LEVELS', () => {
    it('lists A, B, C, D in order', () => {
      expect(EVIDENCE_LEVELS).toEqual(['A', 'B', 'C', 'D']);
    });
  });

  describe('isEvidenceLevel', () => {
    it.each(EVIDENCE_LEVELS)('returns true for "%s"', (l) => {
      expect(isEvidenceLevel(l)).toBe(true);
    });

    it('returns false for other strings', () => {
      expect(isEvidenceLevel('E')).toBe(false);
      expect(isEvidenceLevel('a')).toBe(false);
    });

    it('returns false for non-strings', () => {
      expect(isEvidenceLevel(0)).toBe(false);
      expect(isEvidenceLevel(null)).toBe(false);
    });
  });

  describe('DocumentPhase', () => {
    it('creates a phase without curve', () => {
      const p = DocumentPhase({ type: 'inhale', durationMs: 1000 });
      expect(p).toEqual({ type: 'inhale', durationMs: 1000 });
      expect('curve' in p).toBe(false);
    });

    it('creates a phase with curve', () => {
      const p = DocumentPhase({ type: 'inhale', durationMs: 1000, curve: 'ease-in' });
      expect(p.curve).toBe('ease-in');
    });
  });

  describe('isProtocolDocumentShape', () => {
    it('returns true for a complete document', () => {
      expect(
        isProtocolDocumentShape({
          $schema: 'https://araflow.app/schemas/protocol/v1.json',
          id: 'abc',
          version: '1.0.0',
          title: 'Title',
          breath: { phases: [] },
        }),
      ).toBe(true);
    });

    it('returns false for null', () => {
      expect(isProtocolDocumentShape(null)).toBe(false);
    });

    it('returns false for non-objects', () => {
      expect(isProtocolDocumentShape('string')).toBe(false);
      expect(isProtocolDocumentShape(42)).toBe(false);
    });

    it('returns false when missing $schema', () => {
      expect(
        isProtocolDocumentShape({ id: 'a', version: '1.0.0', title: 't', breath: { phases: [] } }),
      ).toBe(false);
    });

    it('returns false when missing id', () => {
      expect(
        isProtocolDocumentShape({
          $schema: 's',
          version: '1.0.0',
          title: 't',
          breath: { phases: [] },
        }),
      ).toBe(false);
    });

    it('returns false when breath is missing', () => {
      expect(
        isProtocolDocumentShape({ $schema: 's', id: 'a', version: '1.0.0', title: 't' }),
      ).toBe(false);
    });

    it('returns false when breath.phases is not an array', () => {
      expect(
        isProtocolDocumentShape({
          $schema: 's',
          id: 'a',
          version: '1.0.0',
          title: 't',
          breath: { phases: 'not-array' },
        }),
      ).toBe(false);
    });
  });

  describe('hasMetadata', () => {
    it('returns true when metadata is present', () => {
      const doc = {
        $schema: 's',
        id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
        version: '1.0.0' as never,
        title: 't',
        breath: { cycles: 1, phases: [] },
        metadata: { author: 'a' },
      };
      expect(hasMetadata(doc)).toBe(true);
    });

    it('returns false when metadata is absent', () => {
      const doc = {
        $schema: 's',
        id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
        version: '1.0.0' as never,
        title: 't',
        breath: { cycles: 1, phases: [] },
      };
      expect(hasMetadata(doc)).toBe(false);
    });
  });

  describe('computeDeclaredCycleMs', () => {
    it('returns 0 for empty phases', () => {
      expect(computeDeclaredCycleMs({ cycles: 1, phases: [] })).toBe(0);
    });

    it('sums phase durations', () => {
      expect(
        computeDeclaredCycleMs({
          cycles: 1,
          phases: [
            { type: 'inhale', durationMs: 1000 },
            { type: 'hold-in', durationMs: 2000 },
            { type: 'exhale', durationMs: 3000 },
          ],
        }),
      ).toBe(6000);
    });
  });

  describe('computeDeclaredSessionMs', () => {
    it('multiplies cycle by count without rest', () => {
      const ms = computeDeclaredSessionMs({
        cycles: 3,
        phases: [
          { type: 'inhale', durationMs: 1000 },
          { type: 'exhale', durationMs: 1000 },
        ],
      });
      expect(ms).toBe(2000 * 3);
    });

    it('adds restBetweenCyclesMs * (cycles - 1)', () => {
      const ms = computeDeclaredSessionMs({
        cycles: 3,
        restBetweenCyclesMs: 500,
        phases: [
          { type: 'inhale', durationMs: 1000 },
          { type: 'exhale', durationMs: 1000 },
        ],
      });
      expect(ms).toBe(2000 * 3 + 500 * 2);
    });

    it('handles 1 cycle correctly (no rest applied)', () => {
      const ms = computeDeclaredSessionMs({
        cycles: 1,
        restBetweenCyclesMs: 500,
        phases: [
          { type: 'inhale', durationMs: 1000 },
          { type: 'exhale', durationMs: 1000 },
        ],
      });
      expect(ms).toBe(2000);
    });
  });
});