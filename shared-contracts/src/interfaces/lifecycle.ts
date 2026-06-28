/**
 * Lifecycle interfaces — Disposable, Subscription, Engine.
 *
 * These describe the basic lifecycle hooks shared by all engines and
 * resources. Implementations live in @core/timer-engine, @core/breath-engine,
 * @core/protocol-engine, etc.
 */

import type { EngineId } from '../value-objects/ids';
import type { EngineState } from '../enums/state';
import type { Result } from '../patterns/result';

/**
 * Disposable — anything that can be cleaned up.
 */
export interface Disposable {
  /**
   * Releases resources. After dispose, the object is in a terminal state
   * and cannot be reused.
   *
   * MUST be idempotent: calling dispose() twice MUST be safe.
   */
  dispose(): void;

  /**
   * Returns true if dispose() has been called.
   */
  readonly disposed: boolean;
}

/**
 * Subscription — handle returned by event subscriptions.
 */
export interface Subscription {
  /**
   * Stops receiving events. Idempotent.
   */
  unsubscribe(): void;

  /**
   * Returns true if the subscription is still active.
   */
  readonly active: boolean;
}

/**
 * Engine — base interface for all AraFlow engines.
 *
 * Every engine (Timer, Breath, Protocol, Session, Audio, Animation,
 * Analytics, Safety) implements this contract.
 */
export interface Engine {
  /**
   * Unique identifier of this engine instance.
   */
  readonly id: EngineId;

  /**
   * Current lifecycle state of the engine.
   */
  readonly state: EngineState;

  /**
   * Returns a snapshot of the engine's current state for observability.
   */
  snapshot(): unknown;

  /**
   * Subscribes to engine events. Returns a Subscription that can be
   * used to unsubscribe.
   */
  subscribe(listener: (event: unknown) => void): Subscription;

  /**
   * Releases all resources held by the engine. After dispose, the engine
   * cannot be used again.
   */
  dispose(): void;
}

/**
 * LifecycleController — additional methods for engines that support
 * start/pause/resume/stop. Most engines implement this in addition to Engine.
 */
export interface LifecycleController {
  /**
   * Starts the engine. Idempotent if already running.
   * Returns Result to allow non-throwing error propagation.
   */
  start(): Result<void, import('../errors/base').EngineError>;

  /**
   * Pauses the engine. No-op if already paused.
   */
  pause(): Result<void, import('../errors/base').EngineError>;

  /**
   * Resumes from paused state. No-op if not paused.
   */
  resume(): Result<void, import('../errors/base').EngineError>;

  /**
   * Stops the engine. Terminal state; reset() must be called to reuse.
   */
  stop(): Result<void, import('../errors/base').EngineError>;
}