/**
 * RendererColor — snapshot + behavior tests.
 *
 * Sprint 9 — Animation Renderer.
 */

import type { RendererColor } from '../../../src/presentation/animation-renderer';
import {
  rendererColor,
  rendererColorFromHex,
  rendererColorToHex,
  lerpColor,
  withAlpha,
} from '../../../src/presentation/animation-renderer';

describe('RendererColor', () => {
  describe('rendererColor', () => {
    it('constructs an RGBA value with full opacity by default', () => {
      const c = rendererColor(10, 20, 30);
      expect(c).toEqual<RendererColor>({ r: 10, g: 20, b: 30, a: 1 });
    });

    it('respects explicit alpha', () => {
      const c = rendererColor(0, 0, 0, 0.5);
      expect(c.a).toBe(0.5);
    });
  });

  describe('rendererColorFromHex / rendererColorToHex', () => {
    it('parses #RRGGBB into normalized floats', () => {
      const original = rendererColorFromHex('#3366cc');
      expect(original.r).toBeCloseTo(0x33 / 255);
      expect(original.g).toBeCloseTo(0x66 / 255);
      expect(original.b).toBeCloseTo(0xcc / 255);
      expect(original.a).toBe(1);
    });

    it('parses #RRGGBBAA with alpha', () => {
      const original = rendererColorFromHex('#ff00ff80');
      expect(original.r).toBeCloseTo(1);
      expect(original.g).toBeCloseTo(0);
      expect(original.b).toBeCloseTo(1);
      expect(original.a).toBeCloseTo(0x80 / 255);
    });

    it('throws on invalid hex (length mismatch)', () => {
      expect(() => rendererColorFromHex('#xyz')).toThrow();
      expect(() => rendererColorFromHex('not-a-color')).toThrow();
    });

    it('toHex outputs lowercase #RRGGBB', () => {
      expect(rendererColorToHex(rendererColor(1, 0, 1))).toBe('#ff00ff');
    });

    it('toHex clamps out-of-range values to [0, 1]', () => {
      expect(rendererColorToHex(rendererColor(-0.5, 1.5, 0.5))).toBe('#00ff80');
    });
  });

  describe('lerpColor', () => {
    it('returns the from color at t=0', () => {
      const a = rendererColor(0, 0, 0);
      const b = rendererColor(1, 1, 1);
      const mid = lerpColor(a, b, 0);
      expect(mid.r).toBeCloseTo(0);
      expect(mid.g).toBeCloseTo(0);
      expect(mid.b).toBeCloseTo(0);
    });

    it('returns the to color at t=1', () => {
      const a = rendererColor(0, 0, 0);
      const b = rendererColor(1, 1, 1);
      const mid = lerpColor(a, b, 1);
      expect(mid.r).toBeCloseTo(1);
      expect(mid.g).toBeCloseTo(1);
      expect(mid.b).toBeCloseTo(1);
    });

    it('returns the midpoint at t=0.5', () => {
      const a = rendererColor(0, 0, 0);
      const b = rendererColor(1, 0.5, 0.25);
      const mid = lerpColor(a, b, 0.5);
      expect(mid.r).toBeCloseTo(0.5);
      expect(mid.g).toBeCloseTo(0.25);
      expect(mid.b).toBeCloseTo(0.125);
    });

    it('interpolates alpha linearly', () => {
      const a = rendererColor(0, 0, 0, 0);
      const b = rendererColor(0, 0, 0, 1);
      expect(lerpColor(a, b, 0.5).a).toBeCloseTo(0.5);
    });
  });

  describe('withAlpha', () => {
    it('overrides the alpha channel preserving RGB', () => {
      const c = rendererColor(10, 20, 30, 0.9);
      const dim = withAlpha(c, 0.3);
      expect(dim).toEqual({ r: 10, g: 20, b: 30, a: 0.3 });
    });

    it('is immutable — does not mutate the input', () => {
      const c = rendererColor(10, 20, 30, 1);
      withAlpha(c, 0);
      expect(c.a).toBe(1);
    });
  });
});