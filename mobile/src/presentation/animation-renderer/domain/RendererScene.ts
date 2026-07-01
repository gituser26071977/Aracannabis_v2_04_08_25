/**
 * RendererScene — a value-type description of one frame to be drawn.
 *
 * The Renderer produces a RendererScene from an AnimationFrame; the
 * Scene contains the canvas size, the ordered list of commands, and
 * a monotonic timestamp. Scenes are deeply frozen and pure data.
 */

import type { RendererCommand } from './RendererPrimitive';

export interface RendererScene {
  readonly canvasSize: { readonly width: number; readonly height: number };
  readonly commands: readonly RendererCommand[];
  readonly monotonicMs: number;
}

export const buildScene = (
  canvasSize: { width: number; height: number },
  commands: readonly RendererCommand[],
  monotonicMs: number,
): RendererScene =>
  Object.freeze({
    canvasSize: Object.freeze({ width: canvasSize.width, height: canvasSize.height }),
    commands: Object.freeze(commands.map((c) => Object.freeze(c))),
    monotonicMs,
  });
