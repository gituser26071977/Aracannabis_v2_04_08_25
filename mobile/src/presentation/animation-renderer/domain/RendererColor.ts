/**
 * RendererColor — renderer-agnostic color value.
 *
 * Skia implementations consume this as `Color4f` (RGBA float); React
 * Native primitives consume it as `ColorValue` (hex string or rgba
 * object); SVG implementations consume it as a CSS-style string. The
 * Renderer normalizes from a single source so the Animation Engine
 * stays backend-agnostic.
 */

export interface RendererColor {
  readonly r: number;
  readonly g: number;
  readonly b: number;
  readonly a: number;
}

export const rendererColor = (r: number, g: number, b: number, a = 1): RendererColor => ({
  r,
  g,
  b,
  a,
});

export const rendererColorFromHex = (hex: string): RendererColor => {
  const clean = hex.replace('#', '');
  if (clean.length !== 6 && clean.length !== 8) {
    throw new Error(`rendererColorFromHex: invalid hex '${hex}'`);
  }
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;
  const a = clean.length === 8 ? parseInt(clean.substring(6, 8), 16) / 255 : 1;
  return { r, g, b, a };
};

export const rendererColorToHex = (c: RendererColor): string => {
  const toHex = (v: number): string => {
    const n = Math.round(Math.max(0, Math.min(1, v)) * 255);
    return n.toString(16).padStart(2, '0');
  };
  return `#${toHex(c.r)}${toHex(c.g)}${toHex(c.b)}`;
};

export const lerpColor = (from: RendererColor, to: RendererColor, t: number): RendererColor => ({
  r: from.r + (to.r - from.r) * t,
  g: from.g + (to.g - from.g) * t,
  b: from.b + (to.b - from.b) * t,
  a: from.a + (to.a - from.a) * t,
});

export const withAlpha = (c: RendererColor, a: number): RendererColor => ({ ...c, a });
