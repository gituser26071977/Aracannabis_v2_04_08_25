/**
 * AnimationFrameToScene — pure projection from AnimationFrame to
 * RendererScene.
 *
 * This is the seam between the Animation Engine (Core) and the
 * Renderer (Presentation). The Core knows nothing about color, layout,
 * or typography; this projection layer owns those choices. Swapping
 * the renderer backend (RN primitives ↔ Skia ↔ SVG) does not affect
 * the Animation Engine contract.
 *
 * Projection rules:
 *   - The breath circle radius scales from `frame.radius` (0..1) to a
 *     pixel radius up to `maxRadiusPx`.
 *   - The breath circle opacity uses `frame.opacity` (0..1).
 *   - The progress arc fills proportional to `frame.normalizedProgress`
 *     (0..1) around the breath circle.
 *   - The phase label uses `frame.label` (e.g. "Breathe in").
 *   - The remaining time uses `frame.remainingTime` (ms).
 *
 * Pure function: same inputs → same outputs. No side effects.
 */

import type { AnimationFrame } from '@core/animation-engine';

import type { RendererColor } from './RendererColor';
import { lerpColor, rendererColor, withAlpha } from './RendererColor';
import type { RendererCommand } from './RendererPrimitive';
import { arc, circle, text } from './RendererPrimitive';
import type { RendererScene } from './RendererScene';
import { buildScene } from './RendererScene';

export interface FrameToSceneOptions {
  readonly canvasWidth: number;
  readonly canvasHeight: number;
  readonly maxRadiusPx: number;
  readonly breathColor: RendererColor;
  readonly breathStrokeColor: RendererColor;
  readonly trackColor: RendererColor;
  readonly textColor: RendererColor;
  readonly counterColor: RendererColor;
  /** Show the counter (remaining time) on screen. */
  readonly showCounter: boolean;
}

const DEFAULT_OPTIONS: FrameToSceneOptions = {
  canvasWidth: 320,
  canvasHeight: 320,
  maxRadiusPx: 140,
  breathColor: rendererColor(0.4, 0.7, 1.0, 1.0),
  breathStrokeColor: rendererColor(0.2, 0.4, 0.6, 0.6),
  trackColor: rendererColor(0.85, 0.9, 0.95, 0.4),
  textColor: rendererColor(0.1, 0.1, 0.1, 1.0),
  counterColor: rendererColor(0.4, 0.4, 0.4, 0.8),
  showCounter: true,
};

/** Format milliseconds as "MM:SS" or "SSs". */
export const formatRemainingMs = (ms: number): string => {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) {
    return `${seconds}s`;
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
};

/**
 * Project an AnimationFrame to a RendererScene. Pure.
 */
export const animationFrameToScene = (
  frame: AnimationFrame,
  options: Partial<FrameToSceneOptions> = {},
): RendererScene => {
  const opts: FrameToSceneOptions = { ...DEFAULT_OPTIONS, ...options };
  const cx = opts.canvasWidth / 2;
  const cy = opts.canvasHeight / 2;
  const breathRadius = opts.maxRadiusPx * Math.max(0, Math.min(1, frame.radius));
  const breathOpacity = Math.max(0, Math.min(1, frame.opacity));

  const commands: RendererCommand[] = [];

  // Track ring (full circle outline)
  commands.push(
    circle({ x: cx, y: cy }, opts.maxRadiusPx, withAlpha(opts.trackColor, 0.0), opts.trackColor, 4),
  );

  // Progress arc inside the ring
  if (frame.normalizedProgress > 0) {
    commands.push(
      arc(
        { x: cx, y: cy },
        opts.maxRadiusPx,
        -Math.PI / 2,
        2 * Math.PI * frame.normalizedProgress,
        opts.breathStrokeColor,
        4,
      ),
    );
  }

  // Breath circle (filled)
  const fillColor = withAlpha(opts.breathColor, breathOpacity);
  commands.push(
    circle(
      { x: cx, y: cy },
      breathRadius,
      fillColor,
      withAlpha(opts.breathStrokeColor, breathOpacity),
      2,
    ),
  );

  // Phase label (centered)
  commands.push(text({ x: cx, y: cy + 4 }, frame.label, 22, opts.textColor, 'center'));

  // Optional remaining-time counter (below)
  if (opts.showCounter) {
    commands.push(
      text(
        { x: cx, y: cy + opts.maxRadiusPx + 28 },
        formatRemainingMs(frame.remainingTime),
        14,
        opts.counterColor,
        'center',
      ),
    );
  }

  return buildScene(
    { width: opts.canvasWidth, height: opts.canvasHeight },
    commands,
    frame.timestamp,
  );
};

/** Re-export color helpers used by callers building custom scenes. */
export { lerpColor, rendererColor, withAlpha };
