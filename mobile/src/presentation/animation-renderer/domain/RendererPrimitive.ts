/**
 * RendererPrimitive — backend-agnostic draw command.
 *
 * Every command is a tagged union variant. A Renderer translates these
 * to backend calls (Skia `Path/Circle/Text`, React Native `View/Text`,
 * SVG `<circle>/<text>`). The Renderer NEVER mixes commands from
 * different backends — it's a 1:1 translator.
 *
 * Commands are value types (immutable). Consumers compose them in a
 * RendererCommand list to describe a full frame.
 */

import type { RendererColor } from './RendererColor';

export interface Point {
  readonly x: number;
  readonly y: number;
}

export interface Size {
  readonly width: number;
  readonly height: number;
}

export type RendererCommand =
  | {
      readonly kind: 'circle';
      readonly center: Point;
      readonly radius: number;
      readonly fill: RendererColor;
      readonly stroke: RendererColor | null;
      readonly strokeWidth: number;
    }
  | {
      readonly kind: 'text';
      readonly position: Point;
      readonly content: string;
      readonly size: number;
      readonly color: RendererColor;
      readonly align: 'left' | 'center' | 'right';
    }
  | {
      readonly kind: 'arc';
      readonly center: Point;
      readonly radius: number;
      readonly startAngle: number;
      readonly sweepAngle: number;
      readonly color: RendererColor;
      readonly strokeWidth: number;
    }
  | {
      readonly kind: 'rect';
      readonly origin: Point;
      readonly size: Size;
      readonly fill: RendererColor;
    };

/** Build a circle command. */
export const circle = (
  center: Point,
  radius: number,
  fill: RendererColor,
  stroke: RendererColor | null = null,
  strokeWidth = 0,
): RendererCommand => ({
  kind: 'circle',
  center,
  radius,
  fill,
  stroke,
  strokeWidth,
});

/** Build a text command. */
export const text = (
  position: Point,
  content: string,
  size: number,
  color: RendererColor,
  align: 'left' | 'center' | 'right' = 'center',
): RendererCommand => ({
  kind: 'text',
  position,
  content,
  size,
  color,
  align,
});

/** Build an arc command (for progress rings). */
export const arc = (
  center: Point,
  radius: number,
  startAngle: number,
  sweepAngle: number,
  color: RendererColor,
  strokeWidth: number,
): RendererCommand => ({
  kind: 'arc',
  center,
  radius,
  startAngle,
  sweepAngle,
  color,
  strokeWidth,
});

/** Build a rect command. */
export const rect = (origin: Point, size: Size, fill: RendererColor): RendererCommand => ({
  kind: 'rect',
  origin,
  size,
  fill,
});
