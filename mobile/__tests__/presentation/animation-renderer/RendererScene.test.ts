/**
 * RendererScene — snapshot immutability + builder tests.
 *
 * Sprint 9 — Animation Renderer.
 */

import { buildScene, circle, rendererColor } from '../../../src/presentation/animation-renderer';

describe('RendererScene', () => {
  it('builds a scene with the expected shape', () => {
    const scene = buildScene({ width: 320, height: 360 }, [], 1000);
    expect(scene.canvasSize).toEqual({ width: 320, height: 360 });
    expect(scene.commands).toEqual([]);
    expect(scene.monotonicMs).toBe(1000);
  });

  it('freezes the scene deeply', () => {
    const scene = buildScene(
      { width: 100, height: 100 },
      [circle({ x: 0, y: 0 }, 1, rendererColor(0, 0, 0))],
      1,
    );
    expect(Object.isFrozen(scene)).toBe(true);
    expect(Object.isFrozen(scene.canvasSize)).toBe(true);
    expect(Object.isFrozen(scene.commands)).toBe(true);
    expect(Object.isFrozen(scene.commands[0])).toBe(true);
  });

  it('preserves the command order', () => {
    const a = circle({ x: 0, y: 0 }, 1, rendererColor(0, 0, 0));
    const b = circle({ x: 1, y: 1 }, 2, rendererColor(0, 0, 0));
    const scene = buildScene({ width: 10, height: 10 }, [a, b], 0);
    expect(scene.commands[0]).toBe(a);
    expect(scene.commands[1]).toBe(b);
  });
});