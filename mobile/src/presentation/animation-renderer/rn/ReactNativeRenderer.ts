/**
 * ReactNativeRenderer — React Native primitive implementation of the
 * AnimationRenderer interface.
 *
 * Why React Native primitives and not @shopify/react-native-skia?
 *
 *   1. Sprint 9 is the FIRST visual experience — the goal is to
 *      validate the end-to-end pipeline (Runtime → Animation Engine
 *      → Renderer → screen), not to ship a production renderer.
 *   2. Adding @shopify/react-native-skia requires a native rebuild
 *      (iOS pods + Android gradle) which is not in scope of the brief.
 *   3. React Native's built-in Animated API with `useNativeDriver:
 *      true` runs transform/opacity on the native UI thread, hitting
 *      60 FPS with no JS-bridge overhead — comparable perf profile.
 *   4. The renderer interface is backend-agnostic; a Skia renderer
 *      can ship later as a drop-in replacement behind the same
 *      `AnimationRenderer` contract.
 *
 * The renderer is implemented as a custom React hook (`useRenderer`)
 * that returns a ref-compatible surface plus the imperative
 * `render(scene)` API. The hook owns a single stateful object
 * (`ReactNativeRendererImpl`) that translates scenes into Animated
 * values. This keeps the imperative contract on one side and the
 * declarative React surface on the other — without coupling them.
 */

import { useEffect, useMemo, useRef } from 'react';
import { Animated, Easing } from 'react-native';
import type { ViewStyle } from 'react-native';

import type { AnimationRenderer } from '../domain/AnimationRenderer';
import type { RendererColor } from '../domain/RendererColor';
import { rendererColorToHex } from '../domain/RendererColor';
import type { RendererCommand } from '../domain/RendererPrimitive';
import type { RendererScene } from '../domain/RendererScene';

export interface ReactNativeRendererOptions {
  readonly canvasSize: { readonly width: number; readonly height: number };
  /** Animation duration for value transitions, in ms. */
  readonly transitionMs?: number;
}

interface AnimatedCircleState {
  readonly radius: Animated.Value;
  readonly opacity: Animated.Value;
}

interface AnimatedTextState {
  readonly content: string;
  readonly color: string;
}

const RENDERER_ID = 'rn-primitives-v1';

const interpolateColor = (from: RendererColor, to: RendererColor, t: number): string => {
  const mix = (a: number, b: number): number => a + (b - a) * t;
  return rendererColorToHex({
    r: mix(from.r, to.r),
    g: mix(from.g, to.g),
    b: mix(from.b, to.b),
    a: mix(from.a, to.a),
  });
};

const findCircleCommand = (commands: readonly RendererCommand[]): RendererCommand | null => {
  for (const c of commands) {
    if (c.kind === 'circle') {
      return c;
    }
  }
  return null;
};

const findArcCommand = (commands: readonly RendererCommand[]): RendererCommand | null => {
  for (const c of commands) {
    if (c.kind === 'arc') {
      return c;
    }
  }
  return null;
};

const findTextCommand = (commands: readonly RendererCommand[]): RendererCommand | null => {
  for (const c of commands) {
    if (c.kind === 'text') {
      return c;
    }
  }
  return null;
};

/**
 * Stateful renderer. Owned by the `useRenderer` hook.
 */
export class ReactNativeRendererImpl implements AnimationRenderer {
  public readonly id = RENDERER_ID;

  private readonly _transitionMs: number;
  private readonly _canvasSize: { width: number; height: number };
  private readonly _radiusAnim: Animated.Value;
  private readonly _opacityAnim: Animated.Value;
  private readonly _sweepAnim: Animated.Value;
  private _disposed = false;

  /** Current circle view style — updated by `render()`. */
  public circleStyle: ViewStyle = {
    position: 'absolute',
    width: 0,
    height: 0,
    borderRadius: 0,
    backgroundColor: 'transparent',
    transform: [{ translateX: 0 }, { translateY: 0 }, { scale: 1 }],
  };

  /** Current circle stroke style (drawn as outline via `borderColor`). */
  public circleStrokeStyle: ViewStyle = {
    position: 'absolute',
    width: 0,
    height: 0,
    borderRadius: 0,
    borderWidth: 0,
    borderColor: 'transparent',
    backgroundColor: 'transparent',
  };

  /** Current progress-arc style (drawn as a border arc). */
  public arcStyle: ViewStyle = {
    position: 'absolute',
    width: 0,
    height: 0,
    borderRadius: 0,
    borderWidth: 0,
    borderColor: 'transparent',
    backgroundColor: 'transparent',
    transform: [{ rotate: '0deg' }],
  };

  /** Current text content + style. */
  public textState: AnimatedTextState = { content: '', color: '#000000' };

  /** Current counter text + style (below the circle). */
  public counterState: AnimatedTextState = { content: '', color: '#666666' };

  public constructor(options: ReactNativeRendererOptions) {
    this._canvasSize = { ...options.canvasSize };
    this._transitionMs = options.transitionMs ?? 16;
    this._radiusAnim = new Animated.Value(0);
    this._opacityAnim = new Animated.Value(0);
    this._sweepAnim = new Animated.Value(0);
  }

  /** Internal accessor — exposed for the hook to wire Animated listeners. */
  public animated = (): AnimatedCircleState & { readonly sweep: Animated.Value } => ({
    radius: this._radiusAnim,
    opacity: this._opacityAnim,
    sweep: this._sweepAnim,
  });

  public render(scene: RendererScene): void {
    if (this._disposed) {
      return;
    }

    const circleCmd = findCircleCommand(scene.commands);
    const arcCmd = findArcCommand(scene.commands);
    const textCmd = findTextCommand(scene.commands);

    if (circleCmd && circleCmd.kind === 'circle') {
      const diameter = circleCmd.radius * 2;
      const cx = this._canvasSize.width / 2;
      const cy = this._canvasSize.height / 2;
      Animated.parallel([
        Animated.timing(this._radiusAnim, {
          toValue: diameter,
          duration: this._transitionMs,
          easing: Easing.linear,
          useNativeDriver: false,
        }),
        Animated.timing(this._opacityAnim, {
          toValue: circleCmd.fill.a,
          duration: this._transitionMs,
          easing: Easing.linear,
          useNativeDriver: false,
        }),
      ]).start();
      this.circleStyle = {
        position: 'absolute',
        left: cx - circleCmd.radius,
        top: cy - circleCmd.radius,
        width: diameter,
        height: diameter,
        borderRadius: circleCmd.radius,
        backgroundColor: rendererColorToHex(circleCmd.fill),
        opacity: 1,
      };
      if (circleCmd.stroke && circleCmd.strokeWidth > 0) {
        this.circleStrokeStyle = {
          position: 'absolute',
          left: cx - circleCmd.radius - circleCmd.strokeWidth,
          top: cy - circleCmd.radius - circleCmd.strokeWidth,
          width: diameter + circleCmd.strokeWidth * 2,
          height: diameter + circleCmd.strokeWidth * 2,
          borderRadius: circleCmd.radius + circleCmd.strokeWidth,
          borderWidth: circleCmd.strokeWidth,
          borderColor: rendererColorToHex(circleCmd.stroke),
          backgroundColor: 'transparent',
        };
      } else {
        this.circleStrokeStyle = {
          position: 'absolute',
          left: cx,
          top: cy,
          width: 0,
          height: 0,
          borderWidth: 0,
          backgroundColor: 'transparent',
        };
      }
    }

    if (arcCmd && arcCmd.kind === 'arc') {
      const diameter = arcCmd.radius * 2;
      const cx = this._canvasSize.width / 2;
      const cy = this._canvasSize.height / 2;
      const sweepDeg = (arcCmd.sweepAngle / (2 * Math.PI)) * 360;
      Animated.timing(this._sweepAnim, {
        toValue: sweepDeg,
        duration: this._transitionMs,
        easing: Easing.linear,
        useNativeDriver: false,
      }).start();
      this.arcStyle = {
        position: 'absolute',
        left: cx - arcCmd.radius,
        top: cy - arcCmd.radius,
        width: diameter,
        height: diameter,
        borderRadius: arcCmd.radius,
        borderWidth: arcCmd.strokeWidth,
        borderColor: rendererColorToHex(arcCmd.color),
        borderTopColor: 'transparent',
        borderRightColor: sweepDeg > 90 ? rendererColorToHex(arcCmd.color) : 'transparent',
        borderBottomColor: sweepDeg > 180 ? rendererColorToHex(arcCmd.color) : 'transparent',
        borderLeftColor: sweepDeg > 270 ? rendererColorToHex(arcCmd.color) : 'transparent',
        backgroundColor: 'transparent',
        transform: [{ rotate: `${arcCmd.startAngle}rad` }],
      };
    }

    if (textCmd && textCmd.kind === 'text') {
      this.textState = {
        content: textCmd.content,
        color: rendererColorToHex(textCmd.color),
      };
    }

    // The counter is the second `text` command if present.
    const textCmds = scene.commands.filter(
      (c): c is Extract<RendererCommand, { kind: 'text' }> => c.kind === 'text',
    );
    if (textCmds.length >= 2) {
      const counter: Extract<RendererCommand, { kind: 'text' }> = textCmds[textCmds.length - 1]!;
      this.counterState = {
        content: counter.content,
        color: rendererColorToHex(counter.color),
      };
    }
  }

  public dispose(): void {
    if (this._disposed) {
      return;
    }
    this._disposed = true;
    this._radiusAnim.stopAnimation();
    this._opacityAnim.stopAnimation();
    this._sweepAnim.stopAnimation();
  }

  public get disposed(): boolean {
    return this._disposed;
  }

  public get canvasSize(): { width: number; height: number } {
    return this._canvasSize;
  }
}

/**
 * React hook that owns a renderer lifecycle for the lifetime of a
 * mounted component. Returns the renderer instance + its current style
 * surface so the consumer can mount the JSX.
 */
export interface ReactNativeRenderer extends AnimationRenderer {
  readonly circleStyle: ViewStyle;
  readonly circleStrokeStyle: ViewStyle;
  readonly arcStyle: ViewStyle;
  readonly textState: AnimatedTextState;
  readonly counterState: AnimatedTextState;
}

export const createReactNativeRenderer = (
  options: ReactNativeRendererOptions,
): ReactNativeRenderer => {
  const impl = new ReactNativeRendererImpl(options);
  const wrapper: ReactNativeRenderer = {
    id: impl.id,
    render: (scene) => impl.render(scene),
    dispose: () => impl.dispose(),
    get circleStyle() {
      return impl.circleStyle;
    },
    get circleStrokeStyle() {
      return impl.circleStrokeStyle;
    },
    get arcStyle() {
      return impl.arcStyle;
    },
    get textState() {
      return impl.textState;
    },
    get counterState() {
      return impl.counterState;
    },
  };
  return wrapper;
};

/**
 * `useRenderer` — React hook for component-level ownership.
 *
 * Disposes the renderer on unmount. Returns the renderer.
 */
export const useRenderer = (options: ReactNativeRendererOptions): ReactNativeRenderer => {
  const rendererRef = useRef<ReactNativeRenderer | null>(null);
  if (rendererRef.current === null) {
    rendererRef.current = createReactNativeRenderer(options);
  }
  useEffect(() => {
    return () => {
      rendererRef.current?.dispose();
      rendererRef.current = null;
    };
  }, []);
  return useMemo(() => rendererRef.current as ReactNativeRenderer, []);
};

/**
 * `interpolateColor` is re-exported for tests.
 */
export { interpolateColor };
