/**
 * RendererPrimitive — tagged-union + constructor tests.
 *
 * Sprint 9 — Animation Renderer.
 */

import type { RendererCommand } from '../../../src/presentation/animation-renderer';
import {
  circle,
  text,
  arc,
  rect,
  rendererColor,
} from '../../../src/presentation/animation-renderer';

describe('RendererPrimitive', () => {
  describe('circle', () => {
    it('builds a circle command with the expected shape', () => {
      const c: RendererCommand = circle(
        { x: 50, y: 50 },
        20,
        rendererColor(1, 0, 0),
      );
      expect(c.kind).toBe('circle');
      if (c.kind === 'circle') {
        expect(c.radius).toBe(20);
        expect(c.fill.r).toBe(1);
        expect(c.fill.g).toBe(0);
        expect(c.fill.b).toBe(0);
        expect(c.stroke).toBeNull();
        expect(c.strokeWidth).toBe(0);
      }
    });

    it('supports stroke and strokeWidth', () => {
      const c = circle(
        { x: 0, y: 0 },
        10,
        rendererColor(0, 0, 0, 0),
        rendererColor(1, 1, 1),
        2,
      );
      if (c.kind === 'circle') {
        expect(c.strokeWidth).toBe(2);
        expect(c.stroke).not.toBeNull();
        if (c.stroke !== null) {
          expect(c.stroke.r).toBe(1);
        }
      }
    });
  });

  describe('text', () => {
    it('builds a text command with default center alignment', () => {
      const t = text({ x: 10, y: 20 }, 'Inspire', 22, rendererColor(0, 0, 0));
      expect(t.kind).toBe('text');
      if (t.kind === 'text') {
        expect(t.content).toBe('Inspire');
        expect(t.size).toBe(22);
        expect(t.align).toBe('center');
        expect(t.position.x).toBe(10);
        expect(t.position.y).toBe(20);
      }
    });

    it('supports explicit alignment', () => {
      const t = text({ x: 0, y: 0 }, 'x', 12, rendererColor(0, 0, 0), 'left');
      if (t.kind === 'text') {
        expect(t.align).toBe('left');
      }
    });
  });

  describe('arc', () => {
    it('builds an arc command', () => {
      const a = arc(
        { x: 0, y: 0 },
        50,
        0,
        Math.PI,
        rendererColor(0.4, 0.8, 0.2),
        4,
      );
      expect(a.kind).toBe('arc');
      if (a.kind === 'arc') {
        expect(a.radius).toBe(50);
        expect(a.startAngle).toBe(0);
        expect(a.sweepAngle).toBeCloseTo(Math.PI);
        expect(a.strokeWidth).toBe(4);
      }
    });
  });

  describe('rect', () => {
    it('builds a rect command', () => {
      const r = rect(
        { x: 0, y: 0 },
        { width: 100, height: 50 },
        rendererColor(0.8, 0.8, 0.8),
      );
      expect(r.kind).toBe('rect');
      if (r.kind === 'rect') {
        expect(r.size.width).toBe(100);
        expect(r.size.height).toBe(50);
        expect(r.origin.x).toBe(0);
      }
    });
  });

  describe('tagged-union discrimination', () => {
    it('narrows on kind', () => {
      const cmds: RendererCommand[] = [
        circle({ x: 0, y: 0 }, 1, rendererColor(0, 0, 0)),
        text({ x: 0, y: 0 }, 'x', 12, rendererColor(0, 0, 0), 'left'),
        arc({ x: 0, y: 0 }, 1, 0, 1, rendererColor(0, 0, 0), 1),
        rect({ x: 0, y: 0 }, { width: 1, height: 1 }, rendererColor(0, 0, 0)),
      ];
      const kinds = cmds.map((c) => c.kind);
      expect(kinds).toEqual(['circle', 'text', 'arc', 'rect']);
    });
  });
});