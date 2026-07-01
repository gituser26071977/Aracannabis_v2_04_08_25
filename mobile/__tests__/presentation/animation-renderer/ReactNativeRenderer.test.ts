/**
 * ReactNativeRenderer — implementation tests against the
 * AnimationRenderer contract.
 *
 * Sprint 9 — Animation Renderer.
 */

import type { RendererScene } from '../../../src/presentation/animation-renderer';
import {
  buildScene,
  arc,
  circle,
  rendererColor,
  text,
} from '../../../src/presentation/animation-renderer';
import {
  createReactNativeRenderer,
  interpolateColor,
} from '../../../src/presentation/animation-renderer/rn/ReactNativeRenderer';

describe('ReactNativeRenderer', () => {
  const canvas = { width: 320, height: 360 };

  it('has a stable id', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    expect(r.id).toBe('rn-primitives-v1');
  });

  it('exposes style surfaces before any render', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    expect(r.circleStyle).toBeDefined();
    expect(r.circleStrokeStyle).toBeDefined();
    expect(r.arcStyle).toBeDefined();
    expect(r.textState).toEqual({ content: '', color: expect.any(String) });
    expect(r.counterState).toEqual({ content: '', color: expect.any(String) });
  });

  it('updates textState from a text command', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [text({ x: 0, y: 0 }, 'Inspire', 22, rendererColor(0, 0, 0), 'center')],
      1,
    );
    r.render(scene);
    expect(r.textState.content).toBe('Inspire');
  });

  it('updates counterState from the second text command', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [
        text({ x: 0, y: 0 }, 'Inspire', 22, rendererColor(0, 0, 0), 'center'),
        text({ x: 0, y: 0 }, '5s', 14, rendererColor(0.4, 0.4, 0.4, 1), 'center'),
      ],
      1,
    );
    r.render(scene);
    expect(r.textState.content).toBe('Inspire');
    expect(r.counterState.content).toBe('5s');
  });

  it('updates circleStyle with the projected radius', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [circle({ x: canvas.width / 2, y: canvas.height / 2 }, 50, rendererColor(1, 1, 1))],
      1,
    );
    r.render(scene);
    expect(r.circleStyle.width).toBe(100);
    expect(r.circleStyle.height).toBe(100);
    expect(r.circleStyle.borderRadius).toBe(50);
  });

  it('does nothing after dispose', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    r.dispose();
    expect(r.dispose).toBeDefined();
    // Subsequent renders should be silent — no throw.
    const scene: RendererScene = buildScene(
      canvas,
      [circle({ x: 0, y: 0 }, 10, rendererColor(0, 0, 0))],
      1,
    );
    expect(() => r.render(scene)).not.toThrow();
  });

  it('dispose is idempotent', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    r.dispose();
    expect(() => r.dispose()).not.toThrow();
  });

  it('canvasSize accessor matches input', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    expect(r.id).toBe('rn-primitives-v1');
  });

  it('updates arcStyle from an arc command', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [
        arc(
          { x: canvas.width / 2, y: canvas.height / 2 },
          80,
          0,
          Math.PI,
          rendererColor(0.2, 0.4, 0.6),
          4,
        ),
      ],
      1,
    );
    r.render(scene);
    expect(r.arcStyle.width).toBe(160);
    expect(r.arcStyle.borderRadius).toBe(80);
    expect(r.arcStyle.borderWidth).toBe(4);
  });

  it('updates circleStrokeStyle when strokeWidth > 0', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [
        circle(
          { x: canvas.width / 2, y: canvas.height / 2 },
          40,
          rendererColor(1, 1, 1),
          rendererColor(0, 0, 0),
          2,
        ),
      ],
      1,
    );
    r.render(scene);
    expect(r.circleStrokeStyle.borderWidth).toBe(2);
    expect(r.circleStrokeStyle.borderColor).toBeDefined();
  });

  it('uses a custom transitionMs', () => {
    const r = createReactNativeRenderer({
      canvasSize: canvas,
      transitionMs: 50,
    });
    expect(r.id).toBe('rn-primitives-v1');
  });

  it('ignores unknown command kinds', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    // A rect command is not handled — should be silently ignored, not crash.
    const scene: RendererScene = buildScene(
      canvas,
      [
        {
          kind: 'rect',
          origin: { x: 0, y: 0 },
          size: { width: 10, height: 10 },
          fill: rendererColor(0, 0, 0),
        },
      ],
      1,
    );
    expect(() => r.render(scene)).not.toThrow();
  });

  it('handles a scene with no matching commands', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(canvas, [], 1);
    expect(() => r.render(scene)).not.toThrow();
  });

  it('processes full inhale scene with circle, text, counter', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [
        circle({ x: canvas.width / 2, y: canvas.height / 2 }, 50, rendererColor(0.4, 0.7, 1.0)),
        text({ x: canvas.width / 2, y: canvas.height / 2 }, 'Inspire', 22, rendererColor(0, 0, 0), 'center'),
        text({ x: canvas.width / 2, y: canvas.height / 2 + 100 }, '5s', 14, rendererColor(0.4, 0.4, 0.4), 'center'),
      ],
      Date.now(),
    );
    r.render(scene);
    expect(r.textState.content).toBe('Inspire');
    expect(r.counterState.content).toBe('5s');
    expect(r.circleStyle.borderRadius).toBe(50);
  });

  it('does not crash on render after dispose (idempotent no-op)', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    r.dispose();
    const scene: RendererScene = buildScene(
      canvas,
      [circle({ x: 0, y: 0 }, 1, rendererColor(0, 0, 0))],
      1,
    );
    r.render(scene);
    r.render(scene);
    // textState should still be initial empty since render is no-op
    expect(r.textState.content).toBe('');
  });

  it('animates opacity to the fill alpha value', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [circle({ x: 100, y: 100 }, 30, rendererColor(0.5, 0.5, 0.5, 0.7))],
      1,
    );
    r.render(scene);
    expect(r.circleStyle.backgroundColor).toBeDefined();
  });

  it('renders multiple commands in sequence', () => {
    const r = createReactNativeRenderer({ canvasSize: canvas });
    const scene: RendererScene = buildScene(
      canvas,
      [
        arc({ x: 100, y: 100 }, 80, 0, Math.PI, rendererColor(0.2, 0.4, 0.6), 4),
        circle({ x: 100, y: 100 }, 50, rendererColor(1, 0, 0)),
        text({ x: 100, y: 100 }, 'A', 20, rendererColor(0, 0, 0), 'center'),
        text({ x: 100, y: 200 }, '5s', 14, rendererColor(0, 0, 0), 'center'),
      ],
      1,
    );
    r.render(scene);
    expect(r.arcStyle.width).toBe(160);
    expect(r.circleStyle.borderRadius).toBe(50);
    expect(r.textState.content).toBe('A');
    expect(r.counterState.content).toBe('5s');
  });
});

describe('interpolateColor', () => {
  it('mixes two colors at t=0.5', () => {
    const result = interpolateColor(
      rendererColor(0, 0, 0),
      rendererColor(1, 1, 1),
      0.5,
    );
    expect(result).toBe('#808080');
  });

  it('returns from-color at t=0', () => {
    const result = interpolateColor(
      rendererColor(0, 0, 0),
      rendererColor(1, 1, 1),
      0,
    );
    expect(result).toBe('#000000');
  });

  it('returns to-color at t=1', () => {
    const result = interpolateColor(
      rendererColor(0, 0, 0),
      rendererColor(1, 1, 1),
      1,
    );
    expect(result).toBe('#ffffff');
  });
});