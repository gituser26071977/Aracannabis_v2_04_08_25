/**
 * AnimationRenderer — interface contract for rendering AnimationFrames.
 *
 * The interface is the seam between the Animation Engine (Core) and
 * any presentation backend (React Native primitives, Skia, SVG,
 * Canvas). Implementations translate RendererScenes to backend calls.
 *
 * Lifecycle:
 *
 *   const renderer: AnimationRenderer = createRnRenderer(canvasSize);
 *   const scene = animationFrameToScene(frame, opts);
 *   renderer.render(scene); // commits to canvas
 *   renderer.dispose();     // releases resources
 *
 * The interface is minimal: render + dispose. A pure scene projection
 * (`animationFrameToScene`) is exported separately so tests can verify
 * the projection without touching a backend.
 */

import type { RendererScene } from './RendererScene';

export interface AnimationRenderer {
  /** Renderer identifier (e.g. "skia-v1", "rn-primitives-v1"). */
  readonly id: string;
  /** Render a scene. Idempotent within a single frame. */
  render(scene: RendererScene): void;
  /** Release resources (textures, drawables, listeners). */
  dispose(): void;
}

export const ANIMATION_RENDERER_VERSION = '1.0.0' as const;
