/**
 * IR builder tests.
 */

import { buildIR, buildMetadata } from '../../../../src/core/protocol-compiler/ir/IRBuilder';
import {
  fourSevenEightProtocol,
  fullMetadataProtocol,
  minimalValidProtocol,
} from '../fixtures';

describe('IRBuilder', () => {
  describe('buildIR', () => {
    it('builds an IR from a minimal document', () => {
      const ir = buildIR(minimalValidProtocol(), () => 1_700_000_000_000);
      expect(ir.title).toBe('Minimal Protocol');
      expect(ir.breath.cycles).toBe(1);
      expect(ir.breath.phases).toHaveLength(2);
      expect(ir.compiledAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('maps phase types to canonical phases', () => {
      const ir = buildIR(fourSevenEightProtocol(), () => 1_700_000_000_000);
      expect(ir.breath.phases[0]!.phase).toBe('inhaling');
      expect(ir.breath.phases[1]!.phase).toBe('holdAfterInhale');
      expect(ir.breath.phases[2]!.phase).toBe('exhaling');
    });

    it('maps curve types to canonical curves', () => {
      const ir = buildIR(fourSevenEightProtocol(), () => 1_700_000_000_000);
      expect(ir.breath.phases[0]!.curve).toBe('easeInOut');
      expect(ir.breath.phases[1]!.curve).toBe('linear');
    });

    it('defaults missing curve to easeInOut', () => {
      const ir = buildIR(minimalValidProtocol(), () => 1_700_000_000_000);
      expect(ir.breath.phases[0]!.curve).toBe('easeInOut');
    });

    it('computes ratios', () => {
      const ir = buildIR(fourSevenEightProtocol(), () => 1_700_000_000_000);
      // total = 19000; inhale=4000 -> ~0.2105
      expect(ir.breath.phases[0]!.ratio).toBeCloseTo(4000 / 19000, 5);
    });

    it('computes totalCycleMs and totalSessionMs', () => {
      const ir = buildIR(fourSevenEightProtocol(), () => 1_700_000_000_000);
      // cycle = 4000+7000+8000 = 19000
      expect(ir.breath.totalCycleMs).toBe(19000);
      // session = 19000*4 + 1000*3 = 79000
      expect(ir.breath.totalSessionMs).toBe(79000);
    });

    it('preserves metadata fields', () => {
      const ir = buildIR(fullMetadataProtocol(), () => 1_700_000_000_000);
      expect(ir.metadata.author).toBe('Author Name');
      expect(ir.metadata.references).toEqual(['https://pubmed.ncbi.nlm.nih.gov/12345', 'doi:10.1000/xyz123']);
      expect(ir.metadata.category).toBe('wellness');
      expect(ir.metadata.tags).toEqual(['focus', 'energy']);
    });

    it('handles missing metadata with empty defaults', () => {
      const ir = buildIR(minimalValidProtocol(), () => 1_700_000_000_000);
      expect(ir.metadata.references).toEqual([]);
      expect(ir.metadata.contraindications).toEqual([]);
      expect(ir.metadata.tags).toEqual([]);
    });

    it('produces frozen IR', () => {
      const ir = buildIR(minimalValidProtocol(), () => 1_700_000_000_000);
      expect(Object.isFrozen(ir)).toBe(true);
      expect(Object.isFrozen(ir.breath)).toBe(true);
      expect(Object.isFrozen(ir.breath.phases)).toBe(true);
    });
  });

  describe('buildMetadata', () => {
    it('returns empty defaults for missing metadata', () => {
      const md = buildMetadata(minimalValidProtocol());
      expect(md.references).toEqual([]);
      expect(md.contraindications).toEqual([]);
      expect(md.tags).toEqual([]);
    });

    it('copies metadata arrays (no shared reference)', () => {
      const md = buildMetadata(fourSevenEightProtocol());
      expect(md.references).not.toBe(fourSevenEightProtocol().metadata?.references);
    });
  });
});