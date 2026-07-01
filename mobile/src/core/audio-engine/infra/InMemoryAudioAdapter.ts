/**
 * InMemoryAudioAdapter — mock AudioAdapter for tests + Sprint 10 default.
 *
 * Records every call into arrays (`loadLog`, `playLog`, ...). Tests
 * assert on those arrays. No actual audio output. No native deps.
 *
 * Optional `simulatedLatencyMs` adds a small async delay so tests
 * can exercise the async semantics. Default is 0 (synchronous).
 *
 * The adapter is fully in-memory: state is preserved for the
 * lifetime of the instance. `dispose()` is terminal — subsequent
 * calls are no-ops.
 */

import type { Result } from '@araflow/shared-contracts';
import { EngineError, Err, Ok } from '@araflow/shared-contracts';

import type { AudioAdapter, AudioAdapterError } from '../domain/AudioAdapter';
import type { AudioClip } from '../domain/AudioClip';
import type { AudioLayer } from '../domain/AudioLayer';

export interface InMemoryAudioAdapterOptions {
  /** Optional delay before each operation resolves (ms). Default 0. */
  readonly simulatedLatencyMs?: number;
  /**
   * If true, all operations after `dispose()` throw a synthetic
   * EngineError. Default false (idempotent no-ops).
   */
  readonly failAfterDispose?: boolean;
}

export interface InMemoryAudioAdapterSnapshot {
  readonly loadCount: number;
  readonly playCount: number;
  readonly pauseCount: number;
  readonly resumeCount: number;
  readonly stopCount: number;
  readonly setLayerVolumeCount: number;
  readonly setMasterVolumeCount: number;
  readonly disposeCount: number;
}

const ADAPTER_ID = 'in-memory-v1';

export class InMemoryAudioAdapter implements AudioAdapter {
  public readonly id = ADAPTER_ID;

  public readonly loadLog: AudioClip[] = [];
  public readonly playLog: { layer: AudioLayer; clipId: string }[] = [];
  public readonly pauseLog: AudioLayer[] = [];
  public readonly resumeLog: AudioLayer[] = [];
  public readonly stopLog: AudioLayer[] = [];
  public readonly layerVolumeLog: { layer: AudioLayer; value: number }[] = [];
  public readonly masterVolumeLog: number[] = [];
  public disposeCount = 0;

  private readonly _latencyMs: number;
  private readonly _failAfterDispose: boolean;
  private _disposed = false;

  public constructor(options: InMemoryAudioAdapterOptions = {}) {
    this._latencyMs = options.simulatedLatencyMs ?? 0;
    this._failAfterDispose = options.failAfterDispose ?? false;
  }

  public get disposed(): boolean {
    return this._disposed;
  }

  public snapshot = (): InMemoryAudioAdapterSnapshot => ({
    loadCount: this.loadLog.length,
    playCount: this.playLog.length,
    pauseCount: this.pauseLog.length,
    resumeCount: this.resumeLog.length,
    stopCount: this.stopLog.length,
    setLayerVolumeCount: this.layerVolumeLog.length,
    setMasterVolumeCount: this.masterVolumeLog.length,
    disposeCount: this.disposeCount,
  });

  public load = async (clip: AudioClip): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('load')) {
      return Err(this._syntheticError('load'));
    }
    this.loadLog.push(clip);
    await this._delay();
    return Ok(undefined);
  };

  public play = async (
    layer: AudioLayer,
    clipId: string,
  ): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('play')) {
      return Err(this._syntheticError('play'));
    }
    this.playLog.push({ layer, clipId });
    await this._delay();
    return Ok(undefined);
  };

  public pause = async (layer: AudioLayer): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('pause')) {
      return Err(this._syntheticError('pause'));
    }
    this.pauseLog.push(layer);
    await this._delay();
    return Ok(undefined);
  };

  public resume = async (layer: AudioLayer): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('resume')) {
      return Err(this._syntheticError('resume'));
    }
    this.resumeLog.push(layer);
    await this._delay();
    return Ok(undefined);
  };

  public stop = async (layer: AudioLayer): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('stop')) {
      return Err(this._syntheticError('stop'));
    }
    this.stopLog.push(layer);
    await this._delay();
    return Ok(undefined);
  };

  public setLayerVolume = async (
    layer: AudioLayer,
    value: number,
  ): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('setLayerVolume')) {
      return Err(this._syntheticError('setLayerVolume'));
    }
    this.layerVolumeLog.push({ layer, value });
    await this._delay();
    return Ok(undefined);
  };

  public setMasterVolume = async (value: number): Promise<Result<void, AudioAdapterError>> => {
    if (this._guardDisposed('setMasterVolume')) {
      return Err(this._syntheticError('setMasterVolume'));
    }
    this.masterVolumeLog.push(value);
    await this._delay();
    return Ok(undefined);
  };

  public dispose = async (): Promise<Result<void, AudioAdapterError>> => {
    this.disposeCount += 1;
    this._disposed = true;
    await this._delay();
    return Ok(undefined);
  };

  // ─── Internal ───────────────────────────────────────────────────

  private _guardDisposed = (_op: string): boolean => this._disposed && this._failAfterDispose;

  private _syntheticError = (op: string): AudioAdapterError =>
    new EngineError(`in-memory-audio: cannot ${op} after dispose`, {
      code: 'audio_adapter_disposed',
      severity: 'error',
    });

  private _delay = (): Promise<void> =>
    this._latencyMs > 0
      ? new Promise<void>((resolve) => {
          setTimeout(resolve, this._latencyMs);
        })
      : Promise.resolve();
}

export const createInMemoryAudioAdapter = (
  options: InMemoryAudioAdapterOptions = {},
): InMemoryAudioAdapter => new InMemoryAudioAdapter(options);