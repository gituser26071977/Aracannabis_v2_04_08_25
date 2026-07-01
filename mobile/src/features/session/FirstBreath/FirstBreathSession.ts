/**
 * FirstBreathSession — composes the Core engines (Runtime + Animation)
 * with the Renderer (presentation).
 *
 * Pure TypeScript orchestration: no React, no React Native. The
 * Screen consumes this and projects it into JSX. This keeps the
 * orchestration testable without a renderer.
 *
 * Lifecycle:
 *
 *   const session = await FirstBreathSession.start({
 *     protocolSource,
 *     renderer,
 *     now: () => Date.now(),
 *   });
 *   await session.stop();
 */

import type { Result, EngineId } from '@araflow/shared-contracts';
import { EngineError, Err, Ok } from '@araflow/shared-contracts';

import type { AnimationFrame, AnimationEngine, AnimationEvent } from '@core/animation-engine';
import { createAnimation } from '@core/animation-engine';
import type { ProtocolExecutionPlan } from '@core/protocol-compiler';
import { JsonSource } from '@core/protocol-compiler';
import { RuntimeEngine } from '@core/runtime';

import type { AnimationRenderer } from '../../../presentation/animation-renderer';
import { animationFrameToScene } from '../../../presentation/animation-renderer';

export interface FirstBreathSessionOptions {
  readonly protocolSource: string;
  readonly renderer: AnimationRenderer;
  readonly now?: () => number;
}

export type FirstBreathStatus = 'idle' | 'starting' | 'running' | 'paused' | 'stopped' | 'errored';

export interface FirstBreathHandle {
  readonly status: () => FirstBreathStatus;
  readonly currentFrame: () => AnimationFrame;
  readonly protocolTitle: () => string;
  readonly pause: () => void;
  readonly resume: () => void;
  readonly stop: () => Promise<void>;
}

const RUNTIME_ID: EngineId = 'araflow-first-breath-v1' as EngineId;

interface OrchestratorState {
  runtime: RuntimeEngine;
  animation: AnimationEngine;
  status: FirstBreathStatus;
  protocolTitle: string;
  unsubscribeAnimation: () => void;
}

export const startFirstBreathSession = async (
  options: FirstBreathSessionOptions,
): Promise<Result<FirstBreathHandle, EngineError>> => {
  const renderer = options.renderer;
  const now = options.now ?? ((): number => Date.now());

  const runtime = new RuntimeEngine({ runtimeId: RUNTIME_ID });
  const source = JsonSource(options.protocolSource);
  const compileResult = runtime.compile(source);
  if (!compileResult.ok) {
    return Err(compileResult.error);
  }
  const plan: ProtocolExecutionPlan | null = runtime.getExecutionPlan();
  if (plan === null) {
    return Err(
      new EngineError('first-breath: protocol plan is null after compile', {
        code: 'runtime_no_plan',
        severity: 'error',
      }),
    );
  }

  const animation = createAnimation({ runtime });

  const state: OrchestratorState = {
    runtime,
    animation,
    status: 'starting',
    protocolTitle: plan.title,
    unsubscribeAnimation: () => undefined,
  };

  const off = animation.subscribe((event: AnimationEvent) => {
    if (event.type === 'animation-frame') {
      const scene = animationFrameToScene(event.frame);
      renderer.render(scene);
    }
  });
  state.unsubscribeAnimation = off;

  animation.start();
  state.status = 'running';

  const startResult = runtime.start();
  if (!startResult.ok) {
    state.status = 'errored';
    animation.dispose();
    return Err(startResult.error);
  }

  const handle: FirstBreathHandle = {
    status: (): FirstBreathStatus => state.status,
    currentFrame: (): AnimationFrame => animation.currentFrame(),
    protocolTitle: (): string => state.protocolTitle,
    pause: (): void => {
      animation.pause();
      const result = runtime.pause();
      if (result.ok) {
        state.status = 'paused';
      }
    },
    resume: (): void => {
      animation.resume();
      const result = runtime.resume();
      if (result.ok) {
        state.status = 'running';
      }
    },
    stop: async (): Promise<void> => {
      state.status = 'stopped';
      const result = runtime.cancel();
      void result;
      state.unsubscribeAnimation();
      animation.dispose();
      renderer.dispose();
      return Promise.resolve();
    },
  };

  // Drive frames at 60 FPS via a manual update loop. In Sprint 9 we
  // drive via setAnimationFrame; the Engine itself stays
  // independent of the driver.
  const tick = (): void => {
    if (state.status === 'stopped' || state.status === 'errored') {
      return;
    }
    animation.update(now());
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);

  return Ok(handle);
};
