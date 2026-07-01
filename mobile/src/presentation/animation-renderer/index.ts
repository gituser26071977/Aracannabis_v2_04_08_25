/**
 * @presentation/animation-renderer — public barrel.
 *
 * Renderer-agnostic interface for translating AnimationFrames to
 * draw commands. The Skia / RN / SVG implementation lives behind the
 * `AnimationRenderer` interface and is selected at composition time.
 *
 * Sprint 9 deliverable. Core (Animation Engine) is untouched.
 */

export {
  type RendererColor,
  rendererColor,
  rendererColorFromHex,
  rendererColorToHex,
  lerpColor,
  withAlpha,
} from './domain/RendererColor';
export {
  type Point,
  type Size,
  type RendererCommand,
  circle,
  text,
  arc,
  rect,
} from './domain/RendererPrimitive';
export { type RendererScene, buildScene } from './domain/RendererScene';
export {
  type FrameToSceneOptions,
  animationFrameToScene,
  formatRemainingMs,
} from './domain/AnimationFrameToScene';
export { type AnimationRenderer, ANIMATION_RENDERER_VERSION } from './domain/AnimationRenderer';
export {
  createReactNativeRenderer,
  type ReactNativeRenderer,
  type ReactNativeRendererOptions,
} from './rn/ReactNativeRenderer';
