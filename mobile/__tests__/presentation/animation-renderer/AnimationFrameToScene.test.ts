/**
 * AnimationFrameToScene — pure projection tests.
 *
 * Sprint 9 — Animation Renderer.
 */

import type { AnimationFrame } from '../../../src/core/animation-engine';
import {
  animationFrameToScene,
  formatRemainingMs,
  rendererColor,
} from '../../../src/presentation/animation-renderer';

const frame = (overrides: Partial<AnimationFrame> = {}): AnimationFrame => ({
  timestamp: 1000,
  phase: 'inhale',
  normalizedProgress: 0.5,
  radius: 0.7,
  opacity: 0.9,
  scale: 0.5,
  easingCurve: 'easeInOut',
  breathingDepth: 0.7,
  label: 'Inspire',
  remainingTime: 4000,
  ...overrides,
});

describe('formatRemainingMs', () => {
  it('formats seconds when under a minute', () => {
    expect(formatRemainingMs(0)).toBe('0s');
    expect(formatRemainingMs(1000)).toBe('1s');
    expect(formatRemainingMs(4500)).toBe('5s');
  });

  it('formats MM:SS when over a minute', () => {
    expect(formatRemainingMs(60_000)).toBe('1:00');
    expect(formatRemainingMs(65_000)).toBe('1:05');
    expect(formatRemainingMs(125_000)).toBe('2:05');
  });

  it('clamps negative to zero', () => {
    expect(formatRemainingMs(-100)).toBe('0s');
  });
});

describe('animationFrameToScene', () => {
  const opts = {
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

  it('emits a frozen scene with the canvas dimensions', () => {
    const scene = animationFrameToScene(frame(), opts);
    expect(scene.canvasSize).toEqual({ width: 320, height: 320 });
    expect(Object.isFrozen(scene)).toBe(true);
  });

  it('emits 4 commands: track, optional arc, breath circle, label, counter', () => {
    const scene = animationFrameToScene(frame({ normalizedProgress: 0.5 }), opts);
    expect(scene.commands.length).toBe(5);
    expect(scene.commands.map((c) => c.kind)).toEqual([
      'circle', // track ring
      'arc',    // progress arc (because progress > 0)
      'circle', // breath circle
      'text',   // phase label
      'text',   // counter
    ]);
  });

  it('omits the progress arc when normalizedProgress is zero', () => {
    const scene = animationFrameToScene(frame({ normalizedProgress: 0 }), opts);
    expect(scene.commands.map((c) => c.kind)).toEqual(['circle', 'circle', 'text', 'text']);
  });

  it('scales the breath circle radius by frame.radius * maxRadiusPx', () => {
    const scene = animationFrameToScene(frame({ radius: 0.5 }), opts);
    const breathCircle = scene.commands.find((c) => c.kind === 'circle' && c.fill.a > 0);
    expect(breathCircle).toBeDefined();
    if (breathCircle && breathCircle.kind === 'circle') {
      expect(breathCircle.radius).toBeCloseTo(70); // 0.5 * 140
    }
  });

  it('projects the frame label into the text command', () => {
    const scene = animationFrameToScene(frame({ label: 'Segure' }), opts);
    const textCmd = scene.commands.find((c) => c.kind === 'text');
    expect(textCmd).toBeDefined();
    if (textCmd && textCmd.kind === 'text') {
      expect(textCmd.content).toBe('Segure');
    }
  });

  it('formats the remaining time on the counter', () => {
    const scene = animationFrameToScene(frame({ remainingTime: 4500 }), opts);
    const textCmds = scene.commands.filter((c) => c.kind === 'text');
    expect(textCmds[textCmds.length - 1]?.content).toBe('5s');
  });

  it('omits the counter when showCounter is false', () => {
    const scene = animationFrameToScene(frame(), { ...opts, showCounter: false });
    const textCount = scene.commands.filter((c) => c.kind === 'text').length;
    expect(textCount).toBe(1);
  });

  it('clamps radius and opacity to [0, 1] even when out of range', () => {
    const scene = animationFrameToScene(
      frame({ radius: 5, opacity: 5 }),
      opts,
    );
    const breathCircle = scene.commands[2];
    if (breathCircle && breathCircle.kind === 'circle') {
      expect(breathCircle.radius).toBeLessThanOrEqual(140);
      expect(breathCircle.fill.a).toBeLessThanOrEqual(1);
    }
  });

  it('uses the frame timestamp as scene monotonicMs', () => {
    const scene = animationFrameToScene(frame({ timestamp: 9999 }), opts);
    expect(scene.monotonicMs).toBe(9999);
  });
});