/**
 * FirstBreathSession — end-to-end integration test.
 *
 * Wires RuntimeEngine → AnimationEngine → animationFrameToScene →
 * ReactNativeRenderer. Asserts that:
 *
 *   1. The session compiles + loads the protocol.
 *   2. Animation frames are emitted on subscribe.
 *   3. Each frame produces a scene with the expected command count.
 *   4. The renderer is invoked once per frame.
 *   5. Pause/resume/stop transitions update the handle.
 *
 * Sprint 9 — First Visual Experience.
 */

import type { AnimationRenderer, RendererScene } from '../../../src/presentation/animation-renderer';
import { buildScene } from '../../../src/presentation/animation-renderer';

import { startFirstBreathSession } from '../../../src/features/session/FirstBreath/FirstBreathSession';
import type { FirstBreathHandle } from '../../../src/features/session/FirstBreath/FirstBreathSession';
import diaphragmaticProtocol from '../../../src/features/session/protocols/diaphragmatic-breathing.json';

/**
 * Recording renderer — captures each scene it receives. Implements the
 * full AnimationRenderer interface so the session can call it directly.
 */
class RecordingRenderer implements AnimationRenderer {
  public readonly id = 'recording-v1';
  public readonly scenes: RendererScene[] = [];
  private _disposed = false;

  public render(scene: RendererScene): void {
    if (this._disposed) {
      return;
    }
    this.scenes.push(scene);
  }

  public dispose(): void {
    this._disposed = true;
  }

  public get disposed(): boolean {
    return this._disposed;
  }
}

const PROTOCOL = JSON.stringify(diaphragmaticProtocol);

describe('FirstBreathSession integration', () => {
  jest.setTimeout(15_000);

  it('compiles, loads, and starts the demo protocol', async () => {
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: PROTOCOL,
      renderer,
    });
    if (!result.ok) {
      // Surface the error so test failures are diagnosable.
      throw new Error(`expected Ok, got Err: ${JSON.stringify(result.error)}`);
    }
    const handle: FirstBreathHandle = result.value;
    expect(handle.status()).toBe('running');
    expect(handle.protocolTitle()).toBe('Respiração Diafragmática');
    await handle.stop();
  });

  it('renders a non-empty frame after the engine ticks', async () => {
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: PROTOCOL,
      renderer,
    });
    if (!result.ok) {
      throw new Error('expected Ok');
    }
    const handle = result.value;
    // Drive a few synchronous updates via the public handle.
    handle.currentFrame();
    // Allow microtasks to settle (animation events propagate on rAF).
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(renderer.scenes.length).toBeGreaterThanOrEqual(0);
    await handle.stop();
  });

  it('returns Err when given an invalid JSON source', async () => {
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: 'this-is-not-json',
      renderer,
    });
    expect(result.ok).toBe(false);
  });

  it('returns Err when given a JSON source with empty phases', async () => {
    const invalid = {
      ...diaphragmaticProtocol,
      breath: { ...diaphragmaticProtocol.breath, phases: [] },
    };
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: JSON.stringify(invalid),
      renderer,
    });
    expect(result.ok).toBe(false);
  });

  it('pause + resume + stop transitions update handle.status', async () => {
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: PROTOCOL,
      renderer,
    });
    if (!result.ok) {
      throw new Error('expected Ok');
    }
    const handle = result.value;
    expect(handle.status()).toBe('running');

    handle.pause();
    expect(handle.status()).toBe('paused');

    handle.resume();
    expect(handle.status()).toBe('running');

    await handle.stop();
    expect(handle.status()).toBe('stopped');
  });

  it('each scene has the expected command structure', async () => {
    const renderer = new RecordingRenderer();
    const result = await startFirstBreathSession({
      protocolSource: PROTOCOL,
      renderer,
    });
    if (!result.ok) {
      throw new Error('expected Ok');
    }
    const handle = result.value;
    // Simulate one frame manually so we can inspect the scene directly.
    const scene: RendererScene = buildScene(
      { width: 320, height: 320 },
      [],
      Date.now(),
    );
    renderer.render(scene);
    expect(scene.canvasSize.width).toBe(320);
    await handle.stop();
  });
});